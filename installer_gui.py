import tkinter as tk
from tkinter import messagebox, ttk
import winreg
import os
import sys
import urllib.request
import zipfile
import shutil
import subprocess
import threading

REPO_ZIP_URL = "https://github.com/Guimcv1/Juridicode/archive/refs/heads/main.zip"

import ctypes
from ctypes import wintypes

def broadcast_environment_change():
    """Notifies all running Windows processes that the Environment/PATH has changed."""
    try:
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        result = wintypes.DWORD()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Environment",
            SMTO_ABORTIFHUNG,
            2000,
            ctypes.byref(result)
        )
    except Exception:
        pass

def get_install_dir():
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(local_app_data, "Juridicode")

def get_current_paths():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ)
    try:
        current_path, _ = winreg.QueryValueEx(key, "Path")
    except FileNotFoundError:
        current_path = ""
    winreg.CloseKey(key)
    return [p for p in current_path.split(";") if p.strip()]

def set_paths(paths_list):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
    new_path = ";".join(dict.fromkeys(paths_list))
    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
    winreg.CloseKey(key)
    broadcast_environment_change()

def is_installed(directory):
    paths = get_current_paths()
    return any(os.path.normpath(p) == os.path.normpath(directory) for p in paths)

def add_to_path(directory):
    paths = get_current_paths()
    norm_dir = os.path.normpath(directory)
    if not any(os.path.normpath(p) == norm_dir for p in paths):
        paths.append(directory)
        set_paths(paths)
        return True
    return False

def remove_from_path(directory):
    paths = get_current_paths()
    norm_target = os.path.normpath(directory)
    new_paths = [p for p in paths if os.path.normpath(p) != norm_target]
    if len(new_paths) != len(paths):
        set_paths(new_paths)
        return True
    return False

def find_python_executable():
    """Locates the real python.exe on the target machine."""
    # 1. Try which/where python
    for cmd in ["python.exe", "py.exe", "python"]:
        path = shutil.which(cmd)
        if path and not path.lower().endswith("installer_juridico.exe") and not path.lower().endswith("instalador_juridico.exe"):
            return path
            
    # 2. Check current sys.executable if not frozen
    if not getattr(sys, 'frozen', False):
        return sys.executable

    # 3. Check common python paths in LocalAppData
    local_app = os.environ.get("LOCALAPPDATA", "")
    py_base = os.path.join(local_app, "Programs", "Python")
    if os.path.exists(py_base):
        for sub in os.listdir(py_base):
            cand = os.path.join(py_base, sub, "python.exe")
            if os.path.exists(cand):
                return cand

    return "python"

def install_system_shims(install_dir):
    """
    Installs juris.cmd directly into multiple well-known paths that Windows 
    and PowerShell already recognize immediately without needing a full reboot.
    """
    cli_path = os.path.join(install_dir, "cli.py")
    py_exe = find_python_executable()
    
    # CMD script that falls back gracefully
    cmd_content = (
        '@echo off\n'
        f'set "PYTHON_EXE={py_exe}"\n'
        'if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"\n'
        f'"%PYTHON_EXE%" "{cli_path}" %*\n'
    )
    
    candidates = []
    
    # 1. LocalAppData/Microsoft/WindowsApps (default in Windows 10/11 PATH)
    win_apps = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps")
    if os.path.exists(win_apps):
        candidates.append(os.path.join(win_apps, "juris.cmd"))
        
    # 2. Python directory / Scripts folder
    if py_exe != "python" and os.path.exists(py_exe):
        py_dir = os.path.dirname(py_exe)
        py_scripts = os.path.join(py_dir, "Scripts")
        if os.path.exists(py_scripts):
            candidates.append(os.path.join(py_scripts, "juris.cmd"))
        candidates.append(os.path.join(py_dir, "juris.cmd"))

    # 3. Inside the install_dir itself
    candidates.append(os.path.join(install_dir, "juris.cmd"))

    for path in candidates:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(cmd_content)
        except Exception:
            pass

def remove_system_shims(install_dir):
    py_exe = find_python_executable()
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "juris.cmd"),
        os.path.join(install_dir, "juris.cmd")
    ]
    if py_exe != "python" and os.path.exists(py_exe):
        py_dir = os.path.dirname(py_exe)
        candidates.append(os.path.join(py_dir, "Scripts", "juris.cmd"))
        candidates.append(os.path.join(py_dir, "juris.cmd"))

    for path in candidates:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

class OnlineInstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador Online - Juridico.Code")
        self.root.geometry("480x350")
        self.root.configure(bg="#f8fafc")
        self.root.eval('tk::PlaceWindow . center')
        
        self.install_dir = get_install_dir()
        
        self.header = tk.Label(root, text="Juridico.Code Setup", font=("Segoe UI", 16, "bold"), bg="#f8fafc", fg="#0f172a")
        self.header.pack(pady=(20, 4))
        
        self.sub = tk.Label(root, text="Instalação Global do Interpretador Jurídico", font=("Segoe UI", 9), bg="#f8fafc", fg="#64748b")
        self.sub.pack(pady=(0, 10))
        
        self.desc = tk.Label(root, text="", font=("Segoe UI", 9), bg="#f8fafc", fg="#334155", justify=tk.CENTER)
        self.desc.pack(pady=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=360, mode="indeterminate")
        
        self.status_label = tk.Label(root, text="", font=("Segoe UI", 8, "italic"), bg="#f8fafc", fg="#2563eb")
        self.status_label.pack(pady=4)

        self.btn_frame = tk.Frame(root, bg="#f8fafc")
        self.btn_frame.pack(pady=15)
        
        self.update_ui()

    def update_ui(self):
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
            
        installed = is_installed(self.install_dir) and os.path.exists(self.install_dir)
        
        if installed:
            self.desc.config(text=f"O Juridico.Code já está instalado no seu computador!\n\nLocal de Instalação:\n{self.install_dir}")
            
            btn_update = tk.Button(self.btn_frame, text="Atualizar / Reparar", font=("Segoe UI", 10, "bold"), bg="#2563eb", fg="white", padx=14, pady=6, command=self.start_download_and_install, relief=tk.FLAT, cursor="hand2")
            btn_update.grid(row=0, column=0, padx=8)
            
            btn_uninstall = tk.Button(self.btn_frame, text="Desinstalar", font=("Segoe UI", 10, "bold"), bg="#ef4444", fg="white", padx=14, pady=6, command=self.on_uninstall, relief=tk.FLAT, cursor="hand2")
            btn_uninstall.grid(row=0, column=1, padx=8)
        else:
            self.desc.config(text=f"O instalador baixará a versão mais recente do GitHub\n(Guimcv1/Juridicode) e configurará o comando global 'juris'.\n\nDestino:\n{self.install_dir}")
            
            btn_install = tk.Button(self.btn_frame, text="Baixar e Instalar", font=("Segoe UI", 11, "bold"), bg="#10b981", fg="white", padx=20, pady=8, command=self.start_download_and_install, relief=tk.FLAT, cursor="hand2")
            btn_install.pack()

    def start_download_and_install(self):
        self.progress.pack(pady=8)
        self.progress.start(10)
        self.btn_frame.pack_forget()
        self.status_label.config(text="Conectando ao GitHub...")
        
        threading.Thread(target=self._download_and_install_worker, daemon=True).start()

    def _download_and_install_worker(self):
        try:
            temp_zip = os.path.join(os.environ.get("TEMP", "."), "juridicode_repo.zip")
            
            self.status_label.config(text="Baixando repositório Guimcv1/Juridicode...")
            urllib.request.urlretrieve(REPO_ZIP_URL, temp_zip)
            
            self.status_label.config(text="Extraindo arquivos...")
            os.makedirs(self.install_dir, exist_ok=True)
            
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    parts = member.split('/', 1)
                    if len(parts) > 1 and parts[1]:
                        target_file = os.path.join(self.install_dir, parts[1])
                        if member.endswith('/'):
                            os.makedirs(target_file, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(target_file), exist_ok=True)
                            with zip_ref.open(member) as source, open(target_file, "wb") as target:
                                shutil.copyfileobj(source, target)
                                
            self.status_label.config(text="Verificando dependências Python...")
            req_file = os.path.join(self.install_dir, "requirements.txt")
            
            # Find python executable (sys.executable or 'python')
            python_cmd = "python"
            if not getattr(sys, 'frozen', False):
                python_cmd = sys.executable

            # Quick check if core dependencies are already present to avoid slow pip network resolver
            need_install = False
            try:
                check_code = "import fastapi, uvicorn, pydantic, reportlab; print('OK')"
                res = subprocess.run([python_cmd, "-c", check_code], capture_output=True, text=True, timeout=5)
                if "OK" not in res.stdout:
                    need_install = True
            except Exception:
                need_install = True

            if need_install and os.path.exists(req_file):
                self.status_label.config(text="Instalando pacotes necessários...")
                subprocess.run(
                    [python_cmd, "-m", "pip", "install", "-r", req_file, "--no-warn-script-location", "--disable-pip-version-check"],
                    check=False
                )

            self.status_label.config(text="Registrando comando 'juris' no sistema...")
            add_to_path(self.install_dir)
            install_system_shims(self.install_dir)

            self.root.after(0, self._on_install_success)
        except Exception as e:
            self.root.after(0, lambda: self._on_install_error(str(e)))

    def _on_install_success(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_label.config(text="")
        self.btn_frame.pack(pady=15)
        self.update_ui()
        messagebox.showinfo(
            "Instalação Concluída!", 
            f"O Juridico.Code foi instalado com sucesso a partir do GitHub!\n\nVocê já pode abrir qualquer terminal (PowerShell / CMD) e digitar:\n   juris seu_arquivo.jur"
        )

    def _on_install_error(self, err_msg):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_label.config(text="")
        self.btn_frame.pack(pady=15)
        self.update_ui()
        messagebox.showerror("Erro na Instalação", f"Falha ao instalar do GitHub:\n{err_msg}")

    def on_uninstall(self):
        if messagebox.askyesno("Desinstalar", f"Tem certeza que deseja desinstalar o Juridico.Code de:\n{self.install_dir}?"):
            remove_from_path(self.install_dir)
            remove_system_shims(self.install_dir)
            if os.path.exists(self.install_dir):
                try:
                    shutil.rmtree(self.install_dir)
                except Exception as e:
                    messagebox.showwarning("Aviso", f"Não foi possível remover alguns arquivos: {e}")
            messagebox.showinfo("Concluído", "Juridico.Code foi desinstalado do sistema.")
            self.update_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = OnlineInstallerApp(root)
    root.mainloop()
