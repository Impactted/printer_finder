# app/main_app.py
import customtkinter as ctk
from tkinter import ttk
from queue import Queue

from .ui_manager import UIManager
from .scanner import Scanner
from .event_handlers import EventHandlers


class NetworkScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Scanner de Rede v12 (Modular)")
        self.geometry("1200x800")
        self.minsize(1000, 600)
        
        # Configurações de fonte
        self.font_title = ctk.CTkFont(size=24, weight="bold")
        self.font_header = ctk.CTkFont(size=16, weight="bold")
        
        # Configurações da grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Variáveis de estado
        self.queue = Queue()
        self.scanning = False
        self.cancel_flag = False
        self.device_details = {}
        self.completed_count = 0
        self.ip_list = []
        
        # Inicializar componentes
        self.setup_styles()
        self.ui_manager = UIManager(self)
        self.scanner = Scanner(self)
        self.event_handlers = EventHandlers(self)
        
        # Configurar a UI
        self.ui_manager.setup_ui()
        
    def setup_styles(self):
        """Configura os estilos da aplicação."""
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", 
                       fieldbackground="#2a2d2e", rowheight=28)
        style.configure("Treeview.Heading", font=('Segoe UI', 11, 'bold'), 
                       background="#1a1a1a", foreground="white")
        style.map('Treeview', background=[('selected', '#0078d4')])
        style.configure("TProgressbar", thickness=20)
        style.configure("green.Horizontal.TProgressbar", background='#00B050')
        style.configure("red.Horizontal.TProgressbar", background='#C00000')