import tkinter as tk
from tkinter import messagebox
import winreg
import os
import sys

def get_target_directory():
    # If run compiled, we need to get the directory where the .exe is
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    # Otherwise, it's the directory of this script
    return os.path.dirname(os.path.abspath(__file__))

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
    new_path = ";".join(paths_list)
    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
    winreg.CloseKey(key)

def is_installed(directory):
    paths = get_current_paths()
    return directory in paths

def add_to_path():
    target_dir = get_target_directory()
    paths = get_current_paths()
    if target_dir not in paths:
        paths.append(target_dir)
        set_paths(paths)
        return True
    return False

def remove_from_path():
    target_dir = get_target_directory()
    paths = get_current_paths()
    if target_dir in paths:
        paths.remove(target_dir)
        set_paths(paths)
        return True
    return False

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador - Juridico.Code")
        self.root.geometry("450x300")
        self.root.configure(bg="#f8fafc")
        self.root.eval('tk::PlaceWindow . center')
        
        self.target_dir = get_target_directory()
        
        self.header = tk.Label(root, text="Instalador do Motor Jurídico", font=("Segoe UI", 16, "bold"), bg="#f8fafc", fg="#0f172a")
        self.header.pack(pady=(25, 10))
        
        self.desc = tk.Label(root, text="", font=("Segoe UI", 10), bg="#f8fafc", fg="#475569", justify=tk.CENTER)
        self.desc.pack(pady=10)
        
        self.btn_frame = tk.Frame(root, bg="#f8fafc")
        self.btn_frame.pack(pady=20)
        
        self.update_ui()
        
    def update_ui(self):
        # Clear buttons
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
            
        installed = is_installed(self.target_dir)
        
        if installed:
            self.desc.config(text=f"O Motor Jurídico já está instalado e configurado\nno seu computador.\n\nDiretório: {self.target_dir}")
            
            btn_repair = tk.Button(self.btn_frame, text="Reparar Instalação", font=("Segoe UI", 10, "bold"), bg="#2563eb", fg="white", padx=15, pady=6, command=self.on_repair, relief=tk.FLAT, cursor="hand2")
            btn_repair.grid(row=0, column=0, padx=10)
            
            btn_uninstall = tk.Button(self.btn_frame, text="Desinstalar", font=("Segoe UI", 10, "bold"), bg="#ef4444", fg="white", padx=15, pady=6, command=self.on_uninstall, relief=tk.FLAT, cursor="hand2")
            btn_uninstall.grid(row=0, column=1, padx=10)
        else:
            self.desc.config(text=f"Bem-vindo! Este assistente configurará o comando 'juris'\nnas variáveis de ambiente do seu sistema.\n\nDiretório: {self.target_dir}")
            
            btn_install = tk.Button(self.btn_frame, text="Instalar Agora", font=("Segoe UI", 11, "bold"), bg="#10b981", fg="white", padx=20, pady=8, command=self.on_install, relief=tk.FLAT, cursor="hand2")
            btn_install.pack()

    def on_install(self):
        add_to_path()
        messagebox.showinfo("Instalação Concluída", "O comando CLI 'juris' foi instalado com sucesso!\n\nVocê já pode usar 'juris <arquivo>' em qualquer novo terminal.")
        self.update_ui()
        
    def on_uninstall(self):
        if messagebox.askyesno("Desinstalar", "Deseja remover o Juridico.Code do PATH do sistema?"):
            remove_from_path()
            messagebox.showinfo("Desinstalação", "O comando foi removido com sucesso do sistema.")
            self.update_ui()
            
    def on_repair(self):
        # Remove and add again just to be safe
        remove_from_path()
        add_to_path()
        messagebox.showinfo("Reparação", "A configuração do PATH foi refeita com sucesso.")
        self.update_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
