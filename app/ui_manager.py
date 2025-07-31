# app/ui_manager.py
import customtkinter as ctk
from tkinter import ttk
from ui_components import CollapsibleFrame


class UIManager:
    def __init__(self, app):
        self.app = app
        self.collapsible_frames = {}
        self.data_to_export = {}
        
    def setup_ui(self):
        """Configura toda a interface do usuário."""
        self._create_main_frame()
        self._create_header()
        self._create_input_section()
        self._create_button_section()
        self._create_progress_section()
        self._create_results_section()
        
    def _create_main_frame(self):
        """Cria o frame principal."""
        self.main_frame = ctk.CTkFrame(self.app)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
    def _create_header(self):
        """Cria o cabeçalho da aplicação."""
        header = ctk.CTkLabel(self.main_frame, 
                             text="🔍 Scanner de Rede Inteligente", 
                             font=self.app.font_title)
        header.grid(row=0, column=0, columnspan=3, padx=15, pady=(10, 15))
        
    def _create_input_section(self):
        """Cria a seção de entrada de IP."""
        self.ip_entry = ctk.CTkEntry(self.main_frame, 
                                    placeholder_text="Ex: 192.168.0.1 ou 192.168.0.1-255", 
                                    height=35)
        self.ip_entry.grid(row=1, column=0, columnspan=3, padx=15, pady=(0, 10), sticky="ew")
        
    def _create_button_section(self):
        """Cria a seção de botões."""
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        
        self.scan_button = ctk.CTkButton(button_frame, 
                                        text="🚀 Iniciar Scan", 
                                        command=self.app.scanner.start_scan)
        self.scan_button.pack(side="left", padx=15)
        
        self.cancel_button = ctk.CTkButton(button_frame, 
                                          text="⏹️ Cancelar", 
                                          command=self.app.scanner.cancel_scan, 
                                          state="disabled")
        self.cancel_button.pack(side="left")
        
        self.export_button = ctk.CTkButton(button_frame, 
                                          text="📁 Exportar CSV", 
                                          command=self.app.event_handlers.export_csv, 
                                          state="disabled")
        self.export_button.pack(side="right", padx=15)
        
    def _create_progress_section(self):
        """Cria a seção de progresso."""
        self.progress = ttk.Progressbar(self.main_frame, orient="horizontal", mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=3, padx=15, pady=15, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.main_frame, text="Pronto para iniciar.", anchor="w")
        self.status_label.grid(row=4, column=0, columnspan=3, padx=15, sticky="ew")
        
    def _create_results_section(self):
        """Cria a seção de resultados."""
        results_container = ctk.CTkScrollableFrame(self.app, label_text="📊 Resultados do Scan")
        results_container.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        results_container.grid_columnconfigure(0, weight=1)
        
        categories = ["🖨️ Impressoras Encontradas", "💻 Dispositivos Ativos"]
        
        for cat in categories:
            self.data_to_export[cat] = []
            frame = CollapsibleFrame(results_container, cat, self.app)
            frame.pack(fill="x", expand=True, padx=8, pady=3)
            self.collapsible_frames[cat] = frame
            frame.tree.bind("<Double-1>", self.app.event_handlers.show_details_window)
            frame.tree.bind("<Button-3>", self.app.event_handlers.show_context_menu)
            
    def clear_results(self):
        """Limpa todos os resultados da interface."""
        self.progress['value'] = 0
        self.progress.configure(style="default.Horizontal.TProgressbar")
        self.status_label.configure(text="Pronto para iniciar.")
        self.export_button.configure(state="disabled")
        self.app.device_details.clear()
        
        for frame in self.collapsible_frames.values():
            frame.clear()
        for data_list in self.data_to_export.values():
            data_list.clear()
            
    def update_ui_state(self, scanning=False):
        """Atualiza o estado dos controles da UI."""
        if scanning:
            self.scan_button.configure(state="disabled")
            self.cancel_button.configure(state="normal")
        else:
            self.scan_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
            if any(self.data_to_export.values()):
                self.export_button.configure(state="normal")

    def _create_button_section(self):
        """Cria a seção de botões."""
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        
        # Botões principais (esquerda)
        self.scan_button = ctk.CTkButton(button_frame, 
                                        text="🚀 Iniciar Scan", 
                                        command=self.app.scanner.start_scan)
        self.scan_button.pack(side="left", padx=15)
        
        self.cancel_button = ctk.CTkButton(button_frame, 
                                          text="⏹️ Cancelar", 
                                          command=self.app.scanner.cancel_scan, 
                                          state="disabled")
        self.cancel_button.pack(side="left")
        
        # Botão de credenciais (centro)
        self.credentials_button = ctk.CTkButton(button_frame,
                                              text="🔐 Credenciais",
                                              command=self.open_credentials_dialog,
                                              width=120)
        self.credentials_button.pack(side="left", padx=15)
        
        # Botão de exportar (direita)
        self.export_button = ctk.CTkButton(button_frame, 
                                          text="📁 Exportar CSV", 
                                          command=self.app.event_handlers.export_csv, 
                                          state="disabled")
        self.export_button.pack(side="right", padx=15)
        
    def open_credentials_dialog(self):
        """Abre o diálogo de configuração de credenciais."""
        from credentials_dialog import CredentialsDialog
        dialog = CredentialsDialog(self.app)
        self.app.wait_window(dialog)