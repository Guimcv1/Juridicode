import os
import sys
import winreg

def add_to_user_path(directory: str):
    """Adds a directory to Windows User PATH environment variable if not present."""
    directory = os.path.abspath(directory)
    print(f"[*] Registrando diretório no PATH do usuário: {directory}")

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Environment",
        0,
        winreg.KEY_ALL_ACCESS
    )
    try:
        current_path, _ = winreg.QueryValueEx(key, "Path")
    except FileNotFoundError:
        current_path = ""

    paths = [p for p in current_path.split(";") if p.strip()]

    if directory not in paths:
        paths.append(directory)
        new_path = ";".join(paths)
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        print("[SUCESSO] Comando 'juris' adicionado ao PATH do Windows!")
    else:
        print("[INFO] Diretório já está presente no PATH.")

    winreg.CloseKey(key)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    add_to_user_path(base_dir)
    print("\n" + "="*60)
    print("  INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    print("  Agora você pode abrir qualquer terminal e rodar:")
    print("      juris <arquivo.jur>")
    print("="*60 + "\n")
