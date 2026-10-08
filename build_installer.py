import os
import subprocess

def build():
    print("[*] Compilando o Instalador_Juridico.exe com PyInstaller...")
    
    # Clean previous builds
    if os.path.exists("build"):
        import shutil
        shutil.rmtree("build")
        
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name", "Instalador_Juridico",
        "installer_gui.py"
    ]
    
    subprocess.run(cmd, check=True)
    
    print("\n[SUCESSO] Instalador compilado em: dist/Instalador_Juridico.exe")
    print("[INFO] Distribua este arquivo junto com a pasta raiz do projeto.")

if __name__ == "__main__":
    build()
