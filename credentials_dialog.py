# credentials_dialog.py
import customtkinter as ctk
from tkinter import messagebox
import json
import os
from printer_utils import WindowsPrinterManager


class CredentialsDialog(ctk.CTkToplevel):
    """Dialog para configurar credenciais para acesso WMI."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configurar Credenciais de Rede")
        self.geometry("450x400")
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        self.credentials_file = "scanner_credentials.json"
        
        self.setup_ui()
        self.load_saved_credentials()
        
        # Centraliza a janela
        self.center_window()
        
    def center_window(self):
        """Centraliza a janela na tela."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
    def setup_ui(self):
        """Configura a interface do diálogo."""
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, 
                                  text="🔐 Credenciais para Acesso Remoto",
                                  font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(10, 20))
        
        # Explicação
        info_label = ctk.CTkLabel(main_frame,
                                 text="Para obter nomes detalhados das impressoras de alguns computadores,\n"
                                      "é necessário fornecer credenciais de acesso à rede.\n\n"
                                      "⚠️ Deixe em branco para tentar sem credenciais primeiro.",
                                 justify="center")
        info_label.pack(pady=(0, 25))
        
        # Campo usuário
        self.username_label = ctk.CTkLabel(main_frame, text="Usuário:", anchor="w")
        self.username_label.pack(fill="x", padx=20, pady=(0, 5))
        
        self.username_entry = ctk.CTkEntry(main_frame, 
                                          placeholder_text="Ex: Administrador ou DOMINIO\\usuario",
                                          height=35)
        self.username_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        # Campo senha
        self.password_label = ctk.CTkLabel(main_frame, text="Senha:", anchor="w")
        self.password_label.pack(fill="x", padx=20, pady=(0, 5))
        
        self.password_entry = ctk.CTkEntry(main_frame, 
                                          placeholder_text="Senha do usuário",
                                          show="*",
                                          height=35)
        self.password_entry.pack(fill="x", padx=20, pady=(0, 20))
        
        # Checkbox para salvar credenciais
        self.save_credentials_var = ctk.BooleanVar()
        self.save_checkbox = ctk.CTkCheckBox(main_frame,
                                           text="💾 Salvar credenciais localmente (criptografadas)",
                                           variable=self.save_credentials_var)
        self.save_checkbox.pack(pady=(0, 20))
        
        # Frame dos botões
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Botões
        self.test_button = ctk.CTkButton(button_frame,
                                        text="🧪 Testar Conexão",
                                        command=self.test_connection,
                                        width=140)
        self.test_button.pack(side="left", padx=(0, 10))
        
        self.clear_button = ctk.CTkButton(button_frame,
                                         text="🗑️ Limpar",
                                         command=self.clear_fields,
                                         width=100)
        self.clear_button.pack(side="left")
        
        self.cancel_button = ctk.CTkButton(button_frame, 
                                          text="❌ Cancelar",
                                          command=self.cancel_clicked,
                                          width=100)
        self.cancel_button.pack(side="right", padx=(10, 0))
        
        self.ok_button = ctk.CTkButton(button_frame,
                                      text="✅ Aplicar",
                                      command=self.ok_clicked,
                                      width=100)
        self.ok_button.pack(side="right")
        
        # Bind Enter key
        self.bind('<Return>', lambda e: self.ok_clicked())
        
    def clear_fields(self):
        """Limpa os campos de entrada."""
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.save_credentials_var.set(False)
        
    def load_saved_credentials(self):
        """Carrega credenciais salvas anteriormente."""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    data = json.load(f)
                    # Descriptografia simples (apenas para demonstração)
                    username = self._decode(data.get('username', ''))
                    password = self._decode(data.get('password', ''))
                    
                    if username:
                        self.username_entry.insert(0, username)
                    if password:
                        self.password_entry.insert(0, password)
                        
                    self.save_credentials_var.set(True)
        except Exception as e:
            print(f"Erro ao carregar credenciais: {e}")
            
    def save_credentials(self):
        """Salva as credenciais de forma criptografada."""
        if not self.save_credentials_var.get():
            # Remove arquivo se não quer salvar
            if os.path.exists(self.credentials_file):
                try:
                    os.remove(self.credentials_file)
                except:
                    pass
            return
            
        try:
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()
            
            data = {
                'username': self._encode(username),
                'password': self._encode(password)
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(data, f)
                
        except Exception as e:
            print(f"Erro ao salvar credenciais: {e}")
            
    def _encode(self, text: str) -> str:
        """Codificação simples para as credenciais."""
        if not text:
            return ""
        # Base64 simples (não é segurança real, apenas ofuscação)
        import base64
        encoded = text.encode('utf-8')
        return base64.b64encode(encoded).decode('utf-8')
        
    def _decode(self, encoded_text: str) -> str:
        """Decodifica as credenciais."""
        if not encoded_text:
            return ""
        try:
            import base64
            decoded = base64.b64decode(encoded_text.encode('utf-8'))
            return decoded.decode('utf-8')
        except:
            return ""
            
    def test_connection(self):
        """Testa a conexão com as credenciais fornecidas."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # IP de teste (você pode fazer isso configurável)
        test_ip = "192.168.0.109"
        
        self.test_button.configure(text="⏳ Testando...", state="disabled")
        self.update()
        
        try:
            # Define as credenciais temporariamente
            old_username, old_password = WindowsPrinterManager.get_credentials()
            WindowsPrinterManager.set_credentials(username, password)
            
            # Testa a conexão
            printers = WindowsPrinterManager.get_shared_printers(test_ip)
            
            if printers:
                printer_names = [p.get('Name', 'N/A') for p in printers[:3]]
                messagebox.showinfo("✅ Teste Concluído", 
                                   f"Conexão bem-sucedida com {test_ip}!\n\n"
                                   f"Encontradas {len(printers)} impressora(s):\n" + 
                                   "\n".join(f"• {name}" for name in printer_names))
            else:
                messagebox.showwarning("⚠️ Teste Concluído",
                                      f"Conectou ao host {test_ip}, mas nenhuma impressora "
                                      "compartilhada foi encontrada.\n\n"
                                      "Isso pode ser normal se não houver impressoras "
                                      "compartilhadas no host de teste.")
                
        except Exception as e:
            messagebox.showerror("❌ Erro no Teste",
                                f"Não foi possível conectar ao host {test_ip}:\n\n{str(e)}\n\n"
                                "Verifique se:\n"
                                "• O host está acessível na rede\n"
                                "• As credenciais estão corretas\n"
                                "• O WMI está habilitado no host remoto")
        finally:
            # Restaura as credenciais antigas
            WindowsPrinterManager.set_credentials(old_username, old_password)
            self.test_button.configure(text="🧪 Testar Conexão", state="normal")
            
    def ok_clicked(self):
        """Processa o clique no botão OK."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Salva as credenciais se solicitado
        if self.save_credentials_var.get():
            self.save_credentials()
        
        # Define as credenciais globalmente
        WindowsPrinterManager.set_credentials(username if username else None, 
                                             password if password else None)
        
        self.result = {
            'username': username if username else None,
            'password': password if password else None,
            'use_credentials': bool(username and password)
        }
        
        # Mostra confirmação
        if username and password:
            messagebox.showinfo("✅ Credenciais Configuradas", 
                              f"Credenciais configuradas para o usuário: {username}\n\n"
                              "O scanner agora tentará usar estas credenciais "
                              "para obter informações detalhadas das impressoras.")
        else:
            messagebox.showinfo("ℹ️ Modo Sem Credenciais", 
                              "O scanner continuará tentando acessar as impressoras "
                              "sem credenciais específicas.")
            
        self.destroy()
        
    def cancel_clicked(self):
        """Processa o clique no botão Cancelar."""
        self.result = None
        self.destroy()