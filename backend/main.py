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
os.makedirs(STORAGE_DIR, exist_ok=True)
DATABASE_PATH = os.path.join(STORAGE_DIR, "juridicode.sqlite3")
pdf_engine = PDFEngine(storage_dir=STORAGE_DIR)

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
                signed_at TEXT NOT NULL,
                FOREIGN KEY(contract_id) REFERENCES contract_drafts(id)
            );
        """)

initialize_database()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "system": "Juridico Engine v1.0"}

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
        drafts = connection.execute(
            """SELECT id, name, code, formatting_json, created_at, updated_at
               FROM contract_drafts ORDER BY updated_at DESC"""
        ).fetchall()
        signatures = connection.execute(
            """SELECT id, contract_id, signer_name, signer_document, signer_email,
                      document_sha256, signed_at
               FROM contract_signatures ORDER BY signed_at DESC"""
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
        },
        "drafts": [dict(row) for row in drafts],
        "signatures": [dict(row) for row in signatures],
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
            """SELECT signer_name, signer_document, signer_email, signed_at, document_sha256
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
        connection.execute(
            """INSERT INTO contract_signatures
               (id, contract_id, signer_name, signer_document, signer_email,
                consent, document_sha256, signed_at)
               VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
            (signature_id, contract_id, req.signer_name.strip(),
             req.signer_document.strip(), req.signer_email, document_hash, signed_at),
        )
    return {
        "success": True,
        "signature_id": signature_id,
        "document_sha256": document_hash,
        "signed_at": signed_at,
        "notice": "Assinatura eletrônica registrada para auditoria. A validade jurídica depende do método de identificação e da legislação aplicável.",
    }

@app.post("/api/pdf/footer-image")
async def upload_footer_image(file: UploadFile = File(...)):
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="Use uma imagem PNG ou JPG")
    image_path = os.path.join(STORAGE_DIR, f"footer{extension}")
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"success": True, "filename": os.path.basename(image_path)}


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
