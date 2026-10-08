import os

target_cli = os.path.abspath("cli.py")
content = f'@echo off\npython "{target_cli}" %*\n'

locations = [
    r"C:\Users\guimc\AppData\Local\Programs\Python\Python314\Scripts\juris.cmd",
    r"C:\Users\guimc\AppData\Local\Programs\Python\Python314\juris.cmd",
    r"C:\Users\guimc\AppData\Local\Microsoft\WindowsApps\juris.cmd",
]

for loc in locations:
    try:
        os.makedirs(os.path.dirname(loc), exist_ok=True)
        with open(loc, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Instalado em: {loc}")
    except Exception as e:
        print(f"[FALHA] {loc}: {e}")
