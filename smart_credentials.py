# smart_credentials.py
import customtkinter as ctk
from tkinter import messagebox
import json
import os
import base64
import threading
from typing import Optional, Tuple, Callable
from printer_utils import WindowsPrinterManager


class SmartCredentialsManager:
    """Gerenciador inteligente de credenciais que solicita login quando necessário."""
    
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.credentials_file = "scanner_credentials.json"
        self.cached_credentials = {}
        self.failed_hosts = set()
        self.authenticated_hosts = set()
        self.load_saved_credentials()
    
    def load_saved_credentials(self):
        """Carrega credenciais salvas anteriormente."""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    data = json.load(f)
                    username = self._decode(data.get('username', ''))
                    password = self._decode(data.get('password', ''))
                    
                    if username and password:
                        self.cached_credentials = {
                            'username': username,
                            'password': password
                        }
                        # Define as credenciais globalmente
                        WindowsPrinterManager.set_credentials(username, password)
        except Exception as e:
            print(f"Erro ao carregar credenciais: {e}")
    
    def save_credentials(self, username: str, password: str):
        """Salva credenciais de forma criptografada."""
        try:
            data = {
                'username': self._encode(username),
                'password': self._encode(password)
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(data, f)
                
            self.cached_credentials = {
                'username': username,
                'password': password
            }
        except Exception as e:
            print(f"Erro ao salvar credenciais: {e}")
    
    def _encode(self, text: str) -> str:
        """Codificação simples para as credenciais."""
        if not text:
            return ""
        encoded = text.encode('utf-8')
        return base64.b64encode(encoded).decode('utf-8')
        
    def _decode(self, encoded_text: str) -> str:
        """Decodifica as credenciais."""
        if not encoded_text:
            return ""
        try:
            decoded = base64.b64decode(encoded_text.encode('utf-8'))
            return decoded.decode('utf-8')
        except:
            return ""
    
    def request_credentials_if_needed(self, ip: str, operation_name: str = "acessar") -> bool:
        """
        Solicita credenciais se necessário para um host específico.
        
        Args:
            ip (str): Endereço IP do host
            operation_name (str): Nome da operação sendo executada
            
        Returns:
            bool: True se credenciais foram configuradas (ou não necessárias)
        """
        # Se já foi autenticado com sucesso neste host
        if ip in self.authenticated_hosts:
            return True
        
        # Se já falhou antes e usuário cancelou
        if ip in self.failed_hosts:
            return False
        
        # Primeiro tenta com credenciais em cache (se existirem)
        if self.cached_credentials:
            success = self._test_credentials(ip, 
                                           self.cached_credentials['username'], 
                                           self.cached_credentials['password'])
            if success:
                self.authenticated_hosts.add(ip)
                return True
        
        # Se chegou aqui, precisa solicitar credenciais ao usuário
        return self._prompt_for_credentials(ip, operation_name)
    
    def _test_credentials(self, ip: str, username: str, password: str) -> bool:
        """Testa se as credenciais funcionam para um host específico."""
        try:
            # Define credenciais temporariamente
            old_username, old_password = WindowsPrinterManager.get_credentials()
            WindowsPrinterManager.set_credentials(username, password)
            
            # Testa a conexão
            printers = WindowsPrinterManager.get_shared_printers(ip)
            
            # Restaura credenciais antigas
            WindowsPrinterManager.set_credentials(old_username, old_password)
            
            # Se chegou até aqui sem erro, as credenciais funcionam
            return True
