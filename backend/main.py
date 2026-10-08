"""
FastAPI Backend Server for Juridico IDE & Compiler.
Endpoints for Parsing, FSM Simulation, Contradiction Verification, PGP Signing, PDF Generation, and Frontend Static SPA Serving.
"""

import os
import io
import shutil
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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


@app.get("/api/health")
def health_check():
    return {"status": "ok", "system": "Juridico Engine v1.0"}


@app.get("/api/current-file")
def get_current_file():
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
def export_contract_pdf(req: ExecuteRequest):
    try:
        lexer = Lexer(req.code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        evaluator = Evaluator(ast, raw_code=req.code)
        result = evaluator.evaluate(current_runtime_state=req.runtime_state)

        contract_payload = result["contracts"][0] if result["contracts"] else {
            "name": "Instrumento_Padrao",
            "current_state": "EM VIGOR",
            "partes": ["COMPRADOR", "VENDEDOR"],
            "obligations": []
        }
        contract_payload["audit"] = result["audit"]

        out_name = f"Contrato_Auditado_{contract_payload.get('name', 'Doc')}.pdf"
        out_path = os.path.join(STORAGE_DIR, out_name)
        pdf_engine.generate_legal_pdf(contract_payload, out_path)

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
