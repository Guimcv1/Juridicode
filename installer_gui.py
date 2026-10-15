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
import traceback

REPO_ZIP_URL = "https://github.com/Guimcv1/Juridicode/archive/refs/heads/main.zip"
PYTHON_INSTALLER_URL = "https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe"
NODE_ARCHIVE_URL = "https://nodejs.org/dist/v22.14.0/node-v22.14.0-win-x64.zip"
NODE_DIR = r"C:\node"

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
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ)
    except FileNotFoundError:
        return []
    try:
        current_path, _ = winreg.QueryValueEx(key, "Path")
    except FileNotFoundError:
        current_path = ""
    winreg.CloseKey(key)
    return [p for p in current_path.split(";") if p.strip()]

def set_paths(paths_list):
    key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
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
        if path and os.path.basename(path).lower() not in {"python.exe", "py.exe"}:
            continue
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

def find_local_python():
    candidates = []
    local_app = os.environ.get("LOCALAPPDATA", "")
    py_base = os.path.join(local_app, "Programs", "Python")
    if os.path.isdir(py_base):
        for root, _, files in os.walk(py_base):
            if "python.exe" in files:
                candidates.append(os.path.join(root, "python.exe"))
    candidates.extend([
        os.path.join(r"C:\python", "python.exe"),
        os.path.join(r"C:\Python313", "python.exe"),
    ])
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None

def find_python_installer():
    if not os.path.isdir(r"C:\python"):
        return None
    for name in os.listdir(r"C:\python"):
        candidate = os.path.join(r"C:\python", name)
        if (
            os.path.isfile(candidate)
            and name.lower() != "python.exe"
            and name.lower().startswith("python")
            and name.lower().endswith((".exe", ".msi"))
        ):
            return candidate
    return None

def find_npm_executable():
    """Locates npm.cmd without depending on the current shell."""
    for command in ("npm.cmd", "npm.exe", "npm"):
        path = shutil.which(command)
        if path:
            return path
    return None

def find_local_node():
    node_exe = os.path.join(NODE_DIR, "node.exe")
    npm_cmd = os.path.join(NODE_DIR, "npm.cmd")
    if os.path.isfile(node_exe) and os.path.isfile(npm_cmd):
        return node_exe, npm_cmd
    return None, None

def find_node_archive():
    if not os.path.isdir(NODE_DIR):
        return None
    for name in os.listdir(NODE_DIR):
        if name.lower().endswith((".zip", ".msi")):
            return os.path.join(NODE_DIR, name)
    return None

def node_path_entries(node_exe):
    node_dir = os.path.dirname(node_exe)
    npm_bin = os.path.join(node_dir, "node_modules", "npm", "bin")
    return [node_dir, npm_bin]

def configure_node_path(node_exe):
    for directory in node_path_entries(node_exe):
        if os.path.isdir(directory):
            add_to_path(directory)

def describe_missing_tools():
    python_exe = find_python_executable()
    if python_exe == "python" or not os.path.isfile(python_exe):
        python_exe = find_local_python()
    node_exe, npm_exe = find_local_node()
    if not npm_exe:
        npm_exe = find_npm_executable()
        if npm_exe:
            node_exe = shutil.which("node.exe")
    return python_exe, node_exe, npm_exe

def has_python_install_source():
    return bool(find_python_installer())

def has_node_install_source():
    return bool(find_node_archive())

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

    def set_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

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
        python_exe, node_exe, npm_exe = describe_missing_tools()
        missing = []
        if (not python_exe or not os.path.isfile(python_exe)) and not has_python_install_source():
            missing.append("Python")
        if (not node_exe or not npm_exe) and not has_node_install_source():
            missing.append("Node.js")

        if missing:
            tools = " e ".join(missing)
            if not messagebox.askyesno(
                "Dependências necessárias",
                f"{tools} não foi encontrado neste computador.\n\n"
                "Deseja baixar e instalar os componentes oficiais agora?\n"
                "A instalação do Python será apenas para o usuário atual. "
                "O Node.js será instalado em C:\\node quando possível.",
            ):
                return

        self.progress.pack(pady=8)
        self.progress.start(10)
        self.btn_frame.pack_forget()
        self.status_label.config(text="Conectando ao GitHub...")
        
        threading.Thread(target=self._download_and_install_worker, daemon=True).start()

    def _download_file(self, url, destination):
        self.set_status(f"Baixando {os.path.basename(destination)}...")
        urllib.request.urlretrieve(url, destination)

    def _ensure_python(self):
        python_exe, _, _ = describe_missing_tools()
        if python_exe and os.path.isfile(python_exe):
            return python_exe

        installer_dir = r"C:\python"
        os.makedirs(installer_dir, exist_ok=True)
        installer = os.path.join(installer_dir, "python-installer.exe")
        local_installer = find_python_installer()
        if local_installer:
            installer = local_installer
        elif not os.path.isfile(installer):
            self._download_file(PYTHON_INSTALLER_URL, installer)

        self.set_status("Instalando Python para o usuário atual...")
        command = (
            ["msiexec.exe", "/i", installer, "/quiet", "ALLUSERS=2", "Include_pip=1"]
            if installer.lower().endswith(".msi")
            else [installer, "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_pip=1", "SimpleInstall=1"]
        )
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Instalação do Python falhou (código {result.returncode}).")

        python_exe = find_local_python()
        if not python_exe:
            raise RuntimeError("O instalador terminou, mas python.exe não foi encontrado.")
        return python_exe

    def _ensure_node(self):
        node_exe, npm_exe = find_local_node()
        if node_exe and npm_exe:
            configure_node_path(node_exe)
            return node_exe, npm_exe

        os.makedirs(NODE_DIR, exist_ok=True)
        archive = os.path.join(NODE_DIR, "node-install.zip")
        local_archive = find_node_archive()
        if local_archive:
            archive = local_archive
        elif not os.path.isfile(archive):
            self._download_file(NODE_ARCHIVE_URL, archive)

        self.set_status("Instalando Node.js em C:\\node...")
        if archive.lower().endswith(".msi"):
            result = subprocess.run(
                ["msiexec.exe", "/i", archive, "/quiet", "INSTALLDIR=C:\\node"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Instalação do Node.js falhou (código {result.returncode}).")
            node_exe, npm_exe = find_local_node()
            if not node_exe or not npm_exe:
                raise RuntimeError("O instalador terminou, mas node.exe/npm.cmd não foram encontrados em C:\\node.")
            configure_node_path(node_exe)
            return node_exe, npm_exe

        extract_dir = os.path.join(NODE_DIR, "_node_extract")
        if os.path.isdir(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(archive, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        extracted_root = next(
            (os.path.join(extract_dir, name) for name in os.listdir(extract_dir)
             if os.path.isdir(os.path.join(extract_dir, name))),
            None,
        )
        if not extracted_root:
            raise RuntimeError("O arquivo do Node.js não contém uma pasta válida.")
        for name in os.listdir(extracted_root):
            source = os.path.join(extracted_root, name)
            target = os.path.join(NODE_DIR, name)
            if os.path.exists(target):
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)
            shutil.move(source, target)
        shutil.rmtree(extract_dir, ignore_errors=True)

        node_exe, npm_exe = find_local_node()
        if not node_exe or not npm_exe:
            raise RuntimeError("O Node.js foi baixado, mas node.exe/npm.cmd não foram encontrados em C:\\node.")
        configure_node_path(node_exe)
        return node_exe, npm_exe

    def _download_and_install_worker(self):
        try:
            temp_zip = os.path.join(os.environ.get("TEMP", "."), "juridicode_repo.zip")

            self.set_status("Verificando Python e Node.js...")
            python_cmd = self._ensure_python()
            _, npm_cmd = self._ensure_node()
            
            self.set_status("Baixando repositório Guimcv1/Juridicode...")
            urllib.request.urlretrieve(REPO_ZIP_URL, temp_zip)
            
            self.set_status("Extraindo arquivos...")
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

            frontend_dir = os.path.join(self.install_dir, "frontend")
            frontend_dist_index = os.path.join(frontend_dir, "dist", "index.html")
            package_file = os.path.join(frontend_dir, "package.json")

            bundled_frontend = os.path.join(
                getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))),
                "frontend",
                "dist",
            )
            if not os.path.isfile(frontend_dist_index) and os.path.isfile(
                os.path.join(bundled_frontend, "index.html")
            ):
                self.set_status("Instalando a interface React...")
                os.makedirs(os.path.dirname(frontend_dist_index), exist_ok=True)
                shutil.copytree(bundled_frontend, os.path.dirname(frontend_dist_index), dirs_exist_ok=True)

            if os.path.exists(package_file) and not os.path.exists(frontend_dist_index):
                if not npm_cmd:
                    raise RuntimeError(
                        "O Node.js/npm é necessário para preparar a tela React. "
                        "Instale o Node.js LTS e execute o instalador novamente."
                    )

                self.set_status("Preparando a interface React...")
                npm_install = subprocess.run(
                    [npm_cmd, "install", "--no-audit", "--no-fund"],
                    cwd=frontend_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if npm_install.returncode != 0:
                    detail = (npm_install.stderr or npm_install.stdout or "npm install terminou com erro").strip()
                    raise RuntimeError(f"Não foi possível instalar as dependências do React:\n{detail[-2000:]}")

                self.set_status("Compilando a interface React...")
                npm_build = subprocess.run(
                    [npm_cmd, "run", "build"],
                    cwd=frontend_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if npm_build.returncode != 0:
                    detail = (npm_build.stderr or npm_build.stdout or "npm run build terminou com erro").strip()
                    raise RuntimeError(f"Não foi possível compilar a interface React:\n{detail[-2000:]}")

            if os.path.exists(package_file) and not os.path.isfile(frontend_dist_index):
                raise RuntimeError(
                    "A interface React não foi gerada em frontend\\dist\\index.html. "
                    "A instalação foi interrompida para não abrir somente a API."
                )
                                
            self.set_status("Verificando dependências Python...")
            req_file = os.path.join(self.install_dir, "requirements.txt")
            
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
                self.set_status("Instalando pacotes necessários...")
                result = subprocess.run(
                    [python_cmd, "-m", "pip", "install", "-r", req_file, "--no-warn-script-location", "--disable-pip-version-check"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode != 0:
                    detail = (result.stderr or result.stdout or "pip terminou com erro").strip()
                    raise RuntimeError(f"Não foi possível instalar as dependências:\n{detail[-2000:]}")

            self.set_status("Registrando comando 'juris' no sistema...")
            add_to_path(self.install_dir)
            install_system_shims(self.install_dir)

            self.root.after(0, self._on_install_success)
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            self.root.after(0, lambda: self._on_install_error(error))

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
    try:
        root = tk.Tk()
        root.deiconify()
        root.lift()
        root.focus_force()
        app = OnlineInstallerApp(root)
        root.mainloop()
    except Exception:
        error = traceback.format_exc()
        log_path = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "juridicode_installer_error.log")
        try:
            with open(log_path, "w", encoding="utf-8") as log_file:
                log_file.write(error)
        except OSError:
            pass
        try:
            messagebox.showerror(
                "Erro ao abrir o instalador",
                f"A tela não pôde ser aberta.\n\n{error}\n\nDetalhes salvos em:\n{log_path}",
            )
        except Exception:
            pass
