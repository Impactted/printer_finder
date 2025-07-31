# main.py
import customtkinter as ctk
from tkinter import messagebox
import shutil
from app import NetworkScannerApp

def check_nmap():
    """Verifica se o Nmap está acessível no PATH do sistema."""
    return shutil.which('nmap') is not None

if __name__ == "__main__":
    if not check_nmap():
        messagebox.showerror(
            "Nmap não encontrado",
            "O programa Nmap não foi encontrado no PATH do sistema.\n\n"
            "Por favor, instale o Nmap a partir de https://nmap.org e "
            "garanta que a opção para adicioná-lo ao PATH esteja marcada.\n\n"
            "O scanner não pode funcionar sem o Nmap."
        )
    else:
        app = NetworkScannerApp()
        app.mainloop()