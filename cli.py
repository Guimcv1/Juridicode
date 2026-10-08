import sys
import os
import time
import webbrowser
import threading
import urllib.request
import urllib.parse
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend.engine.lexer import Lexer
from backend.engine.parser import Parser
from backend.engine.evaluator import Evaluator

def start_backend_server():
    import uvicorn
    from backend.main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def main():
    if len(sys.argv) < 2:
        print("="*65)
        print("  JURIDICO.CODE - Interpretador & Ambiente Visual Jurídico")
        print("="*65)
        print("Uso: juris <caminho_do_arquivo.jur>")
        print("\nExemplo:")
        print("  juris examples/compra_imovel.jur")
        print("="*65)
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"[ERRO] Arquivo não encontrado: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        code_content = f.read()

    print("\n" + "="*65)
    print(f"  EXECUTANDO CÓDIGO JURÍDICO: {os.path.basename(file_path)}")
    print("="*65)

    # 1. Static check in terminal
    try:
        lexer = Lexer(code_content)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        evaluator = Evaluator(ast, code_content)
        res = evaluator.evaluate()

        print(f"[OK] Tokenização: {len(tokens)} tokens processados.")
        print(f"[OK] AST Construída: {len(ast.contracts)} contrato(s) identificado(s).")
        
        if res.get("contradictions"):
            print(f"[AVISO] {len(res['contradictions'])} contradição(ões) detectada(s):")
            for c in res["contradictions"]:
                print(f"   -> [{c['severity']}] {c['message']}")
        else:
            print("[OK] Nenhuma contradição lógica detectada.")

        print("[OK] Inicializando servidor web e interface interativa...")
    except Exception as e:
        print(f"[ERRO NA COMPILAÇÃO] {e}")

    # 2. Check if server is already running, else start in background thread
    server_running = False
    try:
        resp = urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1)
        if resp.getcode() == 200:
            server_running = True
    except Exception:
        server_running = False

    if not server_running:
        t = threading.Thread(target=start_backend_server, daemon=True)
        t.start()
        # wait for server to boot
        for _ in range(10):
            time.sleep(0.5)
            try:
                if urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1).getcode() == 200:
                    server_running = True
                    break
            except Exception:
                pass

    # 3. Send file content to backend session
    try:
        abs_path = os.path.abspath(file_path)
        req_data = json.dumps({"code": code_content, "path": abs_path}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/current-file",
            data=req_data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req)
    except Exception as e:
        pass

    # 4. Open browser
    url = "http://127.0.0.1:8000"
    print(f"\n[INFO] Abrindo dashboard visual em: {url}")
    print("[INFO] Pressione Ctrl+C para encerrar o ambiente.\n")
    webbrowser.open(url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nAmbiente Juridico.Code encerrado.")

if __name__ == "__main__":
    main()
