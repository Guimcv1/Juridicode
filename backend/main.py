"""
FastAPI Backend Server for Juridico IDE & Compiler.
Endpoints for Parsing, FSM Simulation, Contradiction Verification, PGP Signing, PDF Generation, and Frontend Static SPA Serving.
"""

import os
import io
import shutil
import json
import sqlite3
import hashlib
import datetime
import uuid
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .engine.lexer import Lexer
from .engine.parser import Parser
from .engine.evaluator import Evaluator
from .engine.pdf_engine import PDFEngine

app = FastAPI(
    title="Juridico Language Engine & FSM Server",
    version="1.0.0",
    description="Backend para linguagem jurídica colaborativa, auditável e interpretável."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
COMPANY_IMAGES_DIR = os.path.join(STORAGE_DIR, "company_images")
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(COMPANY_IMAGES_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(STORAGE_DIR, "juridicode.sqlite3")
pdf_engine = PDFEngine(storage_dir=STORAGE_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

CURRENT_FILE_CONTENT = ""
CURRENT_FILE_PATH = ""

class ExecuteRequest(BaseModel):
    code: str
    runtime_state: Optional[Dict[str, Any]] = None

class SetFileRequest(BaseModel):
    code: str
    path: str

class PDFQueryRequest(BaseModel):
    query: str
    filename: Optional[str] = None

class ContractDraftRequest(BaseModel):
    name: str
    code: str
    formatting: Dict[str, Any] = Field(default_factory=dict)

class SignatureRequest(BaseModel):
    signer_name: str
    signer_document: str
    signer_email: Optional[str] = None
    consent: bool

class PDFExportRequest(ExecuteRequest):
    formatting: Dict[str, Any] = Field(default_factory=dict)
    contract_id: Optional[str] = None

def db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database():
    with db_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS contract_drafts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                formatting_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contract_signatures (
                id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                signer_name TEXT NOT NULL,
                signer_document TEXT NOT NULL,
                signer_email TEXT,
                consent INTEGER NOT NULL,
                document_sha256 TEXT NOT NULL,
                certificate_serial TEXT,
                signed_at TEXT NOT NULL,
                FOREIGN KEY(contract_id) REFERENCES contract_drafts(id)
            );
            CREATE TABLE IF NOT EXISTS legal_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                contract_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                fields_json TEXT NOT NULL DEFAULT '[]',
                field_targets_json TEXT NOT NULL DEFAULT '{}',
                source_path TEXT,
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS company_images (
                id TEXT PRIMARY KEY,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL UNIQUE,
                content_type TEXT NOT NULL,
                size INTEGER NOT NULL,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        columns = {
            row["name"] for row in connection.execute(
                "PRAGMA table_info(legal_templates)"
            ).fetchall()
        }
        if "source_path" not in columns:
            connection.execute("ALTER TABLE legal_templates ADD COLUMN source_path TEXT")
        if "is_default" not in columns:
            connection.execute(
                "ALTER TABLE legal_templates ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0"
            )
        if "field_targets_json" not in columns:
            connection.execute(
                "ALTER TABLE legal_templates ADD COLUMN field_targets_json TEXT NOT NULL DEFAULT '{}'"
            )
        signature_columns = {
            row["name"] for row in connection.execute(
                "PRAGMA table_info(contract_signatures)"
            ).fetchall()
        }
        if "certificate_serial" not in signature_columns:
            connection.execute(
                "ALTER TABLE contract_signatures ADD COLUMN certificate_serial TEXT"
            )

initialize_database()


def _names_from_jur_code(code: str) -> Dict[str, str]:
    names = {
        party.strip().lower(): name.strip()
        for party, name in re.findall(
            r"^\s*([A-Za-zÀ-ÿ0-9_]+)\.NOME\s*=\s*[\"']([^\"']+)[\"']",
            code or "",
            flags=re.MULTILINE,
        )
    }
    direct = {
        "contratante": names.get("contratante"),
        "contratado": names.get("contratado"),
    }
    parties = re.search(
        r"^\s*PARTES\s*:\s*(.+)$", code or "", flags=re.MULTILINE | re.IGNORECASE
    )
    if parties:
        party_names = [item.strip().lower() for item in parties.group(1).split(",")]
        if party_names:
            direct["contratante"] = direct["contratante"] or names.get(party_names[0])
        if len(party_names) > 1:
            direct["contratado"] = direct["contratado"] or names.get(party_names[1])
    return {key: value for key, value in direct.items() if value}


def _safe_storage_name(filename: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(filename or "modelo"))


def _company_image_path(stored_name: str) -> str:
    return os.path.join(COMPANY_IMAGES_DIR, _safe_storage_name(stored_name))


def _company_image_record(image_id: str):
    with db_connection() as connection:
        row = connection.execute(
            "SELECT * FROM company_images WHERE id = ?", (image_id,)
        ).fetchone()
    return row


def _template_analysis(content: str, include_heuristic: bool = False):
    explicit = set(re.findall(r"\{\{\s*([^{}]+?)\s*\}\}", content))
    explicit.update(re.findall(r"\[\[\s*([^\[\]]+?)\s*\]\]", content))
    explicit.update(re.findall(r"\$\{\s*([^{}]+?)\s*\}", content))
    targets = {}
    normalized_explicit = set()
    for pattern, wrapper in [
        (r"\{\{\s*([^{}]+?)\s*\}\}", ("{{", "}}")),
        (r"\[\[\s*([^\[\]]+?)\s*\]\]", ("[[", "]]")),
        (r"\$\{\s*([^{}]+?)\s*\}", ("${", "}")),
    ]:
        for field in re.findall(pattern, content):
            clean = field.strip()
            normalized = re.sub(r"\s+", "_", clean).lower()
            if re.fullmatch(r"[A-Za-zÀ-ÿ0-9_.-]+", clean):
                normalized_explicit.add(normalized)
                targets[normalized] = f"{wrapper[0]}{clean}{wrapper[1]}"
    for field in explicit:
        clean = field.strip()
        if re.fullmatch(r"[A-Za-zÀ-ÿ0-9_.-]+", clean):
            normalized = re.sub(r"\s+", "_", clean).lower()
            normalized_explicit.add(normalized)
            targets.setdefault(normalized, field.strip())
    heuristic = {
        "contratante": "CONTRATANTE",
        "contratado": "CONTRATADO",
        "nome_completo": "Nome completo",
        "nacionalidade": "nacionalidade",
        "estado_civil": "estado civil",
        "profissao": "profissão",
        "cpf": "CPF sob o n.",
        "documento_identidade": "CI n.",
        "endereco": "domiciliado(a)",
        "cep": "CEP 74535270",
        "objeto_demanda": "fulano de tal",
        "valor_honorarios": "R$ 70.000,00",
        "parcelas": "1 (uma) parcela",
        "data_assinatura": "data da assinatura",
        "banco": "Banco XXX",
        "agencia": "Agência 0000",
        "conta": "Conta Corrente 00000-0",
        "chave_pix": "Chave PIX e-mail",
        "titularidade": "titularidade Sociedade Individual de Advocacia",
        "endereco_escritorio": "ENDEREÇO",
    }
    if include_heuristic:
        for label, field in [
            ("nome completo", "nome_completo"), ("nome", "nome"),
            ("cpf", "cpf"), ("cnpj", "cnpj"), ("cep", "cep"),
            ("data de nascimento", "data_nascimento"), ("data", "data"),
            ("endereço", "endereco"), ("endereco", "endereco"),
            ("cidade", "cidade"), ("comarca", "comarca"),
            ("profissão", "profissao"), ("profissao", "profissao"),
            ("estado civil", "estado_civil"), ("nacionalidade", "nacionalidade"),
            ("telefone", "telefone"), ("e-mail", "email"), ("email", "email"),
        ]:
            if re.search(rf"(?im)(?:^|[\n;])\s*{re.escape(label)}\s*[:\-_]", content):
                normalized_explicit.add(field)
                targets[field] = label
        for line in content.splitlines():
            match = re.match(r"^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s]{2,40})\s*[:\-]\s*(?:\s*(?:_{2,}|\.{3,}))?\s*$", line)
            if match:
                label = match.group(1).strip()
                plain_label = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
                field = re.sub(r"[^a-z0-9]+", "_", plain_label.lower()).strip("_")
                if field:
                    normalized_explicit.add(field)
                    targets[field] = label
    fields = set(normalized_explicit)
    if include_heuristic:
        fields |= set(heuristic).intersection(
        field for field in heuristic if heuristic[field].lower() in content.lower()
        )
    return sorted(fields), targets


def _template_fields(content: str, include_heuristic: bool = False):
    return _template_analysis(content, include_heuristic)[0]


_DEFAULT_FIELD_TARGETS = {
    "contratante": "CONTRATANTE",
    "contratado": "CONTRATADO",
    "nome_completo": "Nome completo",
    "nacionalidade": "nacionalidade",
    "estado_civil": "estado civil",
    "profissao": "profissão",
    "cpf": "CPF sob o n.",
    "documento_identidade": "CI n.",
    "endereco": "domiciliado(a)",
    "cep": "CEP 74535270",
    "objeto_demanda": "fulano de tal",
    "valor_honorarios": "R$ 70.000,00",
    "parcelas": "1 (uma) parcela",
    "data_assinatura": "data da assinatura",
    "banco": "Banco XXX",
    "agencia": "Agência 0000",
    "conta": "Conta Corrente 00000-0",
    "chave_pix": "Chave PIX e-mail",
    "titularidade": "titularidade Sociedade Individual de Advocacia",
    "endereco_escritorio": "ENDEREÇO",
}


def _read_template_content(file_path: str) -> str:
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".pdf":
        return pdf_engine.extract_text_from_pdf(file_path)
    if extension in {".txt", ".jur", ".md"}:
        with open(file_path, "r", encoding="utf-8") as template_file:
            return template_file.read()
    if extension == ".docx":
        try:
            with zipfile.ZipFile(file_path) as archive:
                root = ET.fromstring(archive.read("word/document.xml"))
            namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            return "\n".join(
                "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
                for paragraph in root.iter(f"{namespace}p")
            )
        except (KeyError, OSError, ET.ParseError) as error:
            raise HTTPException(status_code=400, detail=f"Não foi possível ler o DOCX: {error}") from error
    raise HTTPException(status_code=400, detail="O modelo deve ser PDF, DOCX, TXT, JUR ou MD")


def _find_default_pdf() -> Optional[str]:
    candidates = [
        os.path.join(PROJECT_ROOT, "Contrato Padrão.pdf"),
        os.path.join(PROJECT_ROOT, "Contrato_Padrao.pdf"),
    ]
    candidates.extend(
        os.path.join(PROJECT_ROOT, name)
        for name in os.listdir(PROJECT_ROOT)
        if name.lower().startswith("contrato padra") and name.lower().endswith(".pdf")
    )
    return next((path for path in candidates if os.path.isfile(path)), None)


def _ensure_default_template(connection):
    existing = connection.execute(
        "SELECT id, content, fields_json FROM legal_templates WHERE is_default = 1 LIMIT 1"
    ).fetchone()
    source = _find_default_pdf()
    if existing:
        fields = _template_fields(existing["content"] or "", include_heuristic=True)
        current_fields = json.loads(existing["fields_json"] or "[]")
        if sorted(current_fields) != sorted(fields) and fields:
            connection.execute(
                "UPDATE legal_templates SET fields_json = ? WHERE id = ?",
                (json.dumps(fields, ensure_ascii=False), existing["id"]),
            )
        for template in connection.execute(
            "SELECT id, content, fields_json FROM legal_templates WHERE is_default = 0"
        ).fetchall():
            detected_fields = _template_fields(template["content"] or "")
            if json.loads(template["fields_json"] or "[]") != detected_fields:
                connection.execute(
                    "UPDATE legal_templates SET fields_json = ? WHERE id = ?",
                    (json.dumps(detected_fields, ensure_ascii=False), template["id"]),
                )
        return
    if not source:
        return
    stored_source = os.path.join(STORAGE_DIR, "modelo_padrao.pdf")
    if not os.path.exists(stored_source):
        shutil.copyfile(source, stored_source)
    content = _read_template_content(stored_source).strip()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    connection.execute(
        """INSERT OR IGNORE INTO legal_templates
           (id, name, contract_type, filename, content, fields_json, field_targets_json, source_path,
            is_default, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
        ("default-contract-template", "Contrato Padrão", "Contrato jurídico",
         os.path.basename(source), content,
           json.dumps(_template_fields(content, include_heuristic=True), ensure_ascii=False),
           json.dumps({}, ensure_ascii=False), stored_source,
           now, now),
    )


with db_connection() as _connection:
    _ensure_default_template(_connection)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "system": "Juridico Engine v1.0"}

@app.get("/api/templates")
def list_legal_templates():
    with db_connection() as connection:
        rows = connection.execute(
            """SELECT id, name, contract_type, filename, fields_json, is_default,
                      created_at, updated_at
               FROM legal_templates ORDER BY name"""
        ).fetchall()
    templates = []
    for row in rows:
        item = dict(row)
        item["fields"] = json.loads(item.pop("fields_json") or "[]")
        templates.append(item)
    return {"templates": templates}

@app.get("/api/templates/{template_id}")
def get_legal_template(template_id: str):
    with db_connection() as connection:
        row = connection.execute(
            "SELECT * FROM legal_templates WHERE id = ?", (template_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Modelo jurídico não encontrado")
    item = dict(row)
    item["fields"] = json.loads(item.pop("fields_json") or "[]")
    return item

@app.post("/api/templates/analyze")
async def analyze_legal_template(file: UploadFile = File(...)):
    safe_filename = _safe_storage_name(file.filename or "modelo")
    path = os.path.join(STORAGE_DIR, f"analysis_{uuid.uuid4().hex}_{safe_filename}")
    try:
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        content = _read_template_content(path).strip()
        if not content:
            raise HTTPException(status_code=400, detail="Não foi possível extrair texto do modelo")
        extension = os.path.splitext(file.filename or "")[1].lower()
        fields, field_targets = _template_analysis(content, include_heuristic=True)
        return {
            "success": True,
            "filename": file.filename or safe_filename,
            "file_type": extension.lstrip(".").upper() or "DESCONHECIDO",
            "fields": fields,
            "field_targets": field_targets,
            "preview": content[:2500],
            "message": f"{len(fields)} variável(is) identificada(s). Revise antes de salvar.",
        }
    finally:
        if os.path.exists(path):
            os.remove(path)

@app.post("/api/templates/upload")
async def upload_legal_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    contract_type: str = Form(...),
):
    clean_name = name.strip()
    clean_type = contract_type.strip()
    if not clean_name or not clean_type:
        raise HTTPException(status_code=400, detail="Informe o nome e o tipo do modelo")
    safe_filename = _safe_storage_name(file.filename or "modelo")
    path = os.path.join(STORAGE_DIR, f"template_{uuid.uuid4().hex}_{safe_filename}")
    try:
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        content = _read_template_content(path).strip()
        if not content:
            raise HTTPException(status_code=400, detail="Não foi possível extrair texto do modelo")
        fields, field_targets = _template_analysis(content, include_heuristic=True)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        template_id = str(uuid.uuid4())
        with db_connection() as connection:
            connection.execute(
                """INSERT INTO legal_templates
                   (id, name, contract_type, filename, content, fields_json, field_targets_json, source_path,
                    is_default, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                (template_id, clean_name, clean_type, safe_filename, content,
                 json.dumps(fields, ensure_ascii=False),
                 json.dumps(field_targets, ensure_ascii=False), path, now, now),
            )
        return {
            "success": True,
            "id": template_id,
            "name": clean_name,
            "contract_type": clean_type,
            "fields": fields,
            "preview": content[:700],
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Já existe um modelo com esse nome")

@app.delete("/api/templates/{template_id}")
def delete_legal_template(template_id: str):
    with db_connection() as connection:
        row = connection.execute(
            "SELECT source_path, is_default FROM legal_templates WHERE id = ?",
            (template_id,),
        ).fetchone()
        if row and row["is_default"]:
            raise HTTPException(status_code=400, detail="O modelo padrão não pode ser removido")
        result = connection.execute("DELETE FROM legal_templates WHERE id = ?", (template_id,))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Modelo jurídico não encontrado")
    if row and row["source_path"] and os.path.exists(row["source_path"]):
        os.remove(row["source_path"])
    return {"success": True}

class TemplateGenerateRequest(BaseModel):
    template_id: Optional[str] = None
    code: Optional[str] = None
    fields: Dict[str, Any] = Field(default_factory=dict)
    additions: list[Dict[str, str]] = Field(default_factory=list)
    remove_fields: list[str] = Field(default_factory=list)
    formatting: Dict[str, Any] = Field(default_factory=dict)

@app.post("/api/templates/generate")
def generate_template_pdf(req: TemplateGenerateRequest):
    with db_connection() as connection:
        if req.template_id:
            row = connection.execute(
                "SELECT * FROM legal_templates WHERE id = ?", (req.template_id,)
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT * FROM legal_templates WHERE is_default = 1 LIMIT 1"
            ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Modelo jurídico não encontrado")
    content = row["content"]
    values = {
        str(key): str(value).strip()
        for key, value in req.fields.items()
        if value is not None
    }
    template_fields = json.loads(row["fields_json"] or "[]")
    field_targets = json.loads(row["field_targets_json"] or "{}")
    if req.code:
        values.update(_names_from_jur_code(req.code))
    missing_fields = [
        field for field in template_fields
        if field not in req.remove_fields and not values.get(field, "").strip()
    ]
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Preencha todos os campos obrigatórios antes de exportar.",
                "missing_fields": missing_fields,
            },
        )
    for field in template_fields:
        if field in req.remove_fields:
            content = re.sub(rf"\{{\{{\s*{re.escape(field)}\s*\}}\}}", "", content, flags=re.IGNORECASE)
        else:
            value = values.get(field, f"[{field}]")
            content = re.sub(rf"\{{\{{\s*{re.escape(field)}\s*\}}\}}", value, content, flags=re.IGNORECASE)
    for addition in req.additions:
        title = addition.get("title", "").strip()
        body = addition.get("body", "").strip()
        if title or body:
            content += f"\n\n{title}\n{body}".strip()
    out_name = f"Documento_{_safe_storage_name(row['name'])}.pdf"
    out_path = os.path.join(STORAGE_DIR, out_name)
    pdf_engine.generate_template_pdf(
        title=row["name"],
        contract_type=row["contract_type"],
        content=content,
        output_path=out_path,
        formatting=req.formatting,
        source_pdf=row["source_path"],
        field_replacements={
            field: value for field, value in values.items()
            if field in json.loads(row["fields_json"] or "[]")
        },
        field_targets={**_DEFAULT_FIELD_TARGETS, **field_targets},
    )
    return FileResponse(out_path, filename=out_name, media_type="application/pdf")

@app.get("/api/contracts")
def list_contracts():
    with db_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, created_at, updated_at FROM contract_drafts ORDER BY updated_at DESC"
        ).fetchall()
    return {"contracts": [dict(row) for row in rows]}

@app.get("/api/database/summary")
def database_summary():
    with db_connection() as connection:
        draft_count = connection.execute("SELECT COUNT(*) FROM contract_drafts").fetchone()[0]
        signature_count = connection.execute("SELECT COUNT(*) FROM contract_signatures").fetchone()[0]
        image_count = connection.execute("SELECT COUNT(*) FROM company_images").fetchone()[0]
        drafts = connection.execute(
            """SELECT id, name, code, formatting_json, created_at, updated_at
               FROM contract_drafts ORDER BY updated_at DESC"""
        ).fetchall()
        signatures = connection.execute(
            """SELECT id, contract_id, signer_name, signer_document, signer_email,
                      document_sha256, certificate_serial, signed_at
               FROM contract_signatures ORDER BY signed_at DESC"""
        ).fetchall()
        images = connection.execute(
            """SELECT id, original_name, stored_name, content_type, size, created_at
               FROM company_images ORDER BY created_at DESC"""
        ).fetchall()
    files = [
        {"name": name, "size": os.path.getsize(os.path.join(STORAGE_DIR, name))}
        for name in os.listdir(STORAGE_DIR)
        if os.path.isfile(os.path.join(STORAGE_DIR, name))
    ]
    return {
        "database": os.path.basename(DATABASE_PATH),
        "path": DATABASE_PATH,
        "tables": {
            "contract_drafts": draft_count,
            "contract_signatures": signature_count,
            "company_images": image_count,
        },
        "drafts": [dict(row) for row in drafts],
        "signatures": [dict(row) for row in signatures],
        "company_images": [dict(row) for row in images],
        "storage_files": files,
    }

@app.post("/api/contracts")
def save_contract_draft(req: ContractDraftRequest):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    contract_id = str(uuid.uuid4())
    with db_connection() as connection:
        connection.execute(
            """INSERT INTO contract_drafts
               (id, name, code, formatting_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (contract_id, req.name.strip() or "Rascunho sem nome", req.code,
             json.dumps(req.formatting), now, now),
        )
    return {"success": True, "id": contract_id, "updated_at": now}

@app.get("/api/contracts/{contract_id}")
def get_contract_draft(contract_id: str):
    with db_connection() as connection:
        row = connection.execute(
            "SELECT * FROM contract_drafts WHERE id = ?", (contract_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Rascunho não encontrado")
        signatures = connection.execute(
            """SELECT signer_name, signer_document, signer_email, signed_at,
                      document_sha256, certificate_serial
               FROM contract_signatures WHERE contract_id = ? ORDER BY signed_at""",
            (contract_id,),
        ).fetchall()
    data = dict(row)
    data["formatting"] = json.loads(data.pop("formatting_json") or "{}")
    data["signatures"] = [dict(signature) for signature in signatures]
    return data

@app.put("/api/contracts/{contract_id}")
def update_contract_draft(contract_id: str, req: ContractDraftRequest):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with db_connection() as connection:
        result = connection.execute(
            """UPDATE contract_drafts
               SET name = ?, code = ?, formatting_json = ?, updated_at = ?
               WHERE id = ?""",
            (req.name.strip() or "Rascunho sem nome", req.code,
             json.dumps(req.formatting), now, contract_id),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    return {"success": True, "id": contract_id, "updated_at": now}

@app.post("/api/contracts/{contract_id}/sign")
def sign_contract(contract_id: str, req: SignatureRequest):
    if not req.consent:
        raise HTTPException(status_code=400, detail="O consentimento é obrigatório para assinar")
    with db_connection() as connection:
        row = connection.execute(
            "SELECT code FROM contract_drafts WHERE id = ?", (contract_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Rascunho não encontrado")
        document_hash = hashlib.sha256(row["code"].encode("utf-8")).hexdigest()
        signed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        signature_id = str(uuid.uuid4())
        certificate_serial = f"JUR-{signed_at[:10].replace('-', '')}-{signature_id[:12].upper()}"
        connection.execute(
            """INSERT INTO contract_signatures
               (id, contract_id, signer_name, signer_document, signer_email,
                consent, document_sha256, certificate_serial, signed_at)
               VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)""",
            (signature_id, contract_id, req.signer_name.strip(),
             req.signer_document.strip(), req.signer_email, document_hash,
             certificate_serial, signed_at),
        )
    return {
        "success": True,
        "signature_id": signature_id,
        "document_sha256": document_hash,
        "certificate_serial": certificate_serial,
        "signed_at": signed_at,
        "notice": "Certificado interno de assinatura emitido para auditoria. A validade jurídica depende da identificação, do consentimento e da legislação aplicável.",
    }

@app.post("/api/pdf/footer-image")
async def upload_footer_image(file: UploadFile = File(...)):
    return await upload_company_image(file)


@app.get("/api/company-images")
def list_company_images():
    with db_connection() as connection:
        rows = connection.execute(
            """SELECT id, original_name, stored_name, content_type, size, created_at
               FROM company_images ORDER BY created_at DESC"""
        ).fetchall()
    return {"images": [dict(row) for row in rows]}


@app.post("/api/company-images")
async def upload_company_image(file: UploadFile = File(...)):
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="Use uma imagem PNG ou JPG")
    image_id = str(uuid.uuid4())
    stored_name = f"{image_id}{extension}"
    image_path = _company_image_path(stored_name)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    size = os.path.getsize(image_path)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with db_connection() as connection:
        connection.execute(
            """INSERT INTO company_images
               (id, original_name, stored_name, content_type, size, path, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (image_id, file.filename or stored_name, stored_name,
             file.content_type or "application/octet-stream", size, image_path, now),
        )
    return {
        "success": True,
        "id": image_id,
        "filename": stored_name,
        "original_name": file.filename or stored_name,
        "message": "Imagem da empresa salva em backend/storage/company_images e registrada no SQLite.",
    }


@app.get("/api/current-file")
def get_current_file():
    global CURRENT_FILE_CONTENT, CURRENT_FILE_PATH
    if CURRENT_FILE_PATH and os.path.exists(CURRENT_FILE_PATH):
        try:
            with open(CURRENT_FILE_PATH, "r", encoding="utf-8") as f:
                CURRENT_FILE_CONTENT = f.read()
        except Exception:
            pass
    return {"code": CURRENT_FILE_CONTENT, "path": CURRENT_FILE_PATH}


@app.post("/api/current-file")
def set_current_file(req: SetFileRequest):
    global CURRENT_FILE_CONTENT, CURRENT_FILE_PATH
    CURRENT_FILE_CONTENT = req.code
    CURRENT_FILE_PATH = req.path
    return {"status": "updated", "length": len(req.code), "path": CURRENT_FILE_PATH}

@app.post("/api/save-document")
def save_document(req: ExecuteRequest):
    global CURRENT_FILE_CONTENT, CURRENT_FILE_PATH
    try:
        if not CURRENT_FILE_PATH:
            return JSONResponse(status_code=400, content={"success": False, "error": "Nenhum arquivo ativo para salvar."})
        
        with open(CURRENT_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(req.code)
            
        CURRENT_FILE_CONTENT = req.code
        return {"success": True, "message": f"Arquivo salvo com sucesso em {CURRENT_FILE_PATH}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/api/execute")
def execute_code(req: ExecuteRequest):
    try:
        global CURRENT_FILE_CONTENT
        CURRENT_FILE_CONTENT = req.code

        lexer = Lexer(req.code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        evaluator = Evaluator(ast, raw_code=req.code)
        result = evaluator.evaluate(current_runtime_state=req.runtime_state)
        
        result["tokens_count"] = len(tokens)
        result["raw_code"] = req.code
        return result
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )


@app.post("/api/verify-contradictions")
def verify_contradictions(req: ExecuteRequest):
    try:
        lexer = Lexer(req.code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        evaluator = Evaluator(ast, raw_code=req.code)
        result = evaluator.evaluate(current_runtime_state=req.runtime_state)
        return {
            "success": True,
            "contradictions": result["contradictions"],
            "total_found": len(result["contradictions"])
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.post("/api/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(STORAGE_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        text_preview = pdf_engine.extract_text_from_pdf(file_path)[:500]
        return {
            "success": True,
            "filename": file.filename,
            "preview": text_preview,
            "message": "Documento PDF indexado com sucesso no banco de dados de precedentes."
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.get("/api/pdf/list")
def list_pdfs():
    files = [f for f in os.listdir(STORAGE_DIR) if f.lower().endswith(".pdf")]
    return {"files": files}


@app.post("/api/pdf/query")
def query_pdf(req: PDFQueryRequest):
    results = pdf_engine.query_pdf_knowledge_base(req.query, req.filename)
    return {"success": True, "results": results}


@app.post("/api/export/pdf")
def export_contract_pdf(req: PDFExportRequest):
    try:
        lexer = Lexer(req.code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        evaluator = Evaluator(ast, raw_code=req.code)
        result = evaluator.evaluate(current_runtime_state=req.runtime_state)

        if not result["contracts"]:
            raise HTTPException(
                status_code=400,
                detail="O arquivo .jur não contém nenhum CONTRATO para exportar.",
            )
        contract_payload = result["contracts"][0]
        contract_payload["audit"] = result["audit"]
        signatures = []
        if req.contract_id:
            with db_connection() as connection:
                signatures = [
                    dict(row) for row in connection.execute(
                        """SELECT signer_name, signer_document, signer_email, signed_at,
                                  document_sha256, certificate_serial
                           FROM contract_signatures WHERE contract_id = ? ORDER BY signed_at""",
                        (req.contract_id,),
                    ).fetchall()
                ]
        contract_payload["signatures"] = signatures

        out_name = f"Contrato_Auditado_{contract_payload.get('name', 'Doc')}.pdf"
        out_path = os.path.join(STORAGE_DIR, out_name)
        pdf_engine.generate_legal_pdf(
            contract_payload,
            out_path,
            formatting=req.formatting,
            footer_image=req.formatting.get("footer_image"),
        )

        return FileResponse(out_path, filename=out_name, media_type="application/pdf")
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"success": False, "error": str(e), "trace": traceback.format_exc()})


@app.get("/api/contracts/{contract_id}/signed-pdf")
def export_signed_contract_pdf(contract_id: str):
    with db_connection() as connection:
        contract = connection.execute(
            "SELECT name, code, formatting_json FROM contract_drafts WHERE id = ?",
            (contract_id,),
        ).fetchone()
        signatures = [
            dict(row) for row in connection.execute(
                """SELECT signer_name, signer_document, signer_email, signed_at,
                          document_sha256, certificate_serial
                   FROM contract_signatures WHERE contract_id = ? ORDER BY signed_at""",
                (contract_id,),
            ).fetchall()
        ]
    if not contract:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    if not signatures:
        raise HTTPException(status_code=400, detail="O documento ainda não possui assinaturas")
    try:
        lexer = Lexer(contract["code"])
        tokens = lexer.tokenize()
        ast = Parser(tokens).parse()
        result = Evaluator(ast, raw_code=contract["code"]).evaluate()
        if not result["contracts"]:
            raise HTTPException(status_code=400, detail="O arquivo .jur não contém contrato")
        payload = result["contracts"][0]
        payload["audit"] = result["audit"]
        payload["signatures"] = signatures
        out_name = f"Contrato_Assinado_{_safe_storage_name(contract['name'])}.pdf"
        out_path = os.path.join(STORAGE_DIR, out_name)
        pdf_engine.generate_legal_pdf(
            payload,
            out_path,
            formatting=json.loads(contract["formatting_json"] or "{}"),
        )
        return FileResponse(out_path, filename=out_name, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as error:
        return JSONResponse(status_code=400, content={"success": False, "error": str(error)})

# Serve compiled frontend if exists
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Endpoint API não encontrado")
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend dist index.html não encontrado")
