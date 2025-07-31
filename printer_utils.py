# printer_utils.py
import subprocess
import platform
import socket
import re
import os
from typing import List, Dict, Optional


class WindowsPrinterManager:
    """Classe para gerenciar operações relacionadas a impressoras Windows."""
    
    # Variáveis de classe para credenciais globais
    _global_username = None
    _global_password = None
    _use_credentials = False
    
    @classmethod
    def set_credentials(cls, username: str = None, password: str = None):
        """Define credenciais globais para acesso WMI."""
        cls._global_username = username
        cls._global_password = password
        cls._use_credentials = bool(username and password)
    
    @classmethod
    def get_credentials(cls):
        """Retorna as credenciais configuradas."""
        return cls._global_username, cls._global_password
    
    @staticmethod
    def get_shared_printers(ip: str) -> Optional[List[Dict[str, str]]]:
        """
        Obtém a lista de impressoras compartilhadas de um host Windows.
        Tenta diferentes métodos em ordem de prioridade.
        
        Args:
            ip (str): Endereço IP do host Windows
            
        Returns:
            List[Dict[str, str]] | None: Lista de impressoras ou None se erro/não Windows
        """
        if platform.system() != "Windows":
            return None
        
        # Método 1: Tentar com credenciais se configuradas
        if WindowsPrinterManager._use_credentials:
            printers = WindowsPrinterManager._try_wmi_with_credentials(ip)
            if printers:
                return printers
        
        # Método 2: Tentar WMI sem credenciais
        printers = WindowsPrinterManager._try_wmi_without_credentials(ip)
        if printers:
            return printers
        
        # Método 3: Usar NET VIEW para listar compartilhamentos
        printers = WindowsPrinterManager._try_net_view(ip)
        if printers:
            return printers
        
        # Método 4: Tentar PowerShell remoto
        printers = WindowsPrinterManager._try_powershell_remote(ip)
        if printers:
            return printers
        
        # Método 5: Tentar reg query para registro remoto
        printers = WindowsPrinterManager._try_registry_query(ip)
        if printers:
            return printers
        
        return None
    
    @staticmethod
    def _try_wmi_with_credentials(ip: str) -> Optional[List[Dict[str, str]]]:
        """Tenta usar WMI com credenciais configuradas."""
        try:
            username, password = WindowsPrinterManager.get_credentials()
            if not username or not password:
                return None
                
            command = [
                'wmic', f'/node:{ip}', f'/user:{username}', f'/password:{password}',
                'printer', 'get', 
                'Name,ShareName,Default,Status,DriverName,Location,Comment',
                '/format:csv'
            ]
            
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=15, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return WindowsPrinterManager._parse_wmic_output(result.stdout)
                
        except Exception as e:
            print(f"WMI com credenciais falhou para {ip}: {e}")
        
        return None
    
    @staticmethod
    def _try_wmi_without_credentials(ip: str) -> Optional[List[Dict[str, str]]]:
        """Tenta usar WMI sem credenciais explícitas."""
        try:
            command = [
                'wmic', f'/node:{ip}', 'printer', 'get', 
                'Name,ShareName,Default,Status,DriverName,Location,Comment',
                '/format:csv'
            ]
            
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=10, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return WindowsPrinterManager._parse_wmic_output(result.stdout)
                
        except Exception as e:
            print(f"WMI sem credenciais falhou para {ip}: {e}")
        
        return None
    
    @staticmethod
    def _try_net_view(ip: str) -> Optional[List[Dict[str, str]]]:
        """Usa o comando NET VIEW para listar compartilhamentos."""
        try:
            # Primeiro tenta sem credenciais
            command = ['net', 'view', f'\\\\{ip}']
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return WindowsPrinterManager._parse_net_view_output(result.stdout, ip)
            
            # Se falhou e tem credenciais, tenta com credenciais
            if WindowsPrinterManager._use_credentials:
                username, password = WindowsPrinterManager.get_credentials()
                if username and password:
                    # Mapeia temporariamente um drive para autenticar
                    map_cmd = ['net', 'use', f'\\\\{ip}\\IPC$', password, f'/user:{username}']
                    map_result = subprocess.run(map_cmd, capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    if map_result.returncode == 0:
                        # Tenta o NET VIEW novamente
                        result = subprocess.run(command, capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
                        if result.returncode == 0:
                            printers = WindowsPrinterManager._parse_net_view_output(result.stdout, ip)
                            # Limpa a conexão
                            subprocess.run(['net', 'use', f'\\\\{ip}\\IPC$', '/delete'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                            return printers
                
        except Exception as e:
            print(f"NET VIEW falhou para {ip}: {e}")
        
        return None
    
    @staticmethod
    def _try_powershell_remote(ip: str) -> Optional[List[Dict[str, str]]]:
        """Tenta usar PowerShell para acessar impressoras remotas."""
        try:
            if WindowsPrinterManager._use_credentials:
                username, password = WindowsPrinterManager.get_credentials()
                if username and password:
                    # PowerShell com credenciais
                    ps_command = f'''
                    $secpass = ConvertTo-SecureString "{password}" -AsPlainText -Force
                    $cred = New-Object PSCredential("{username}", $secpass)
                    try {{
                        Get-WmiObject -Class Win32_Printer -ComputerName {ip} -Credential $cred | 
                        Where-Object {{$_.Shared -eq $true}} | 
                        Select-Object Name,ShareName,DriverName,Location,Comment | 
                        ConvertTo-Csv -NoTypeInformation
                    }} catch {{
                        Write-Output "ERROR: $_"
                    }}
                    '''
                else:
                    return None
            else:
                # PowerShell sem credenciais
                ps_command = f'''
                try {{
                    Get-WmiObject -Class Win32_Printer -ComputerName {ip} | 
                    Where-Object {{$_.Shared -eq $true}} | 
                    Select-Object Name,ShareName,DriverName,Location,Comment | 
                    ConvertTo-Csv -NoTypeInformation
                }} catch {{
                    Write-Output "ERROR: $_"
                }}
                '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=20,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and not result.stdout.startswith("ERROR"):
                return WindowsPrinterManager._parse_powershell_output(result.stdout)
                
        except Exception as e:
            print(f"PowerShell remoto falhou para {ip}: {e}")
        
        return None
    
    @staticmethod
    def _try_registry_query(ip: str) -> Optional[List[Dict[str, str]]]:
        """Tenta acessar o registro remoto para encontrar impressoras."""
        try:
            if WindowsPrinterManager._use_credentials:
                username, password = WindowsPrinterManager.get_credentials()
                if username and password:
                    # Conecta ao registro remoto com credenciais
                    connect_cmd = ['reg', 'query', f'\\\\{ip}\\HKLM\\SYSTEM\\CurrentControlSet\\Control\\Print\\Printers', '/s']
                    # Não há opção direta de usuário/senha no reg query, então usamos runas
                    runas_cmd = f'runas /user:{username} /savecred "reg query \\\\\\\\{ip}\\\\HKLM\\\\SYSTEM\\\\CurrentControlSet\\\\Control\\\\Print\\\\Printers /s"'
                    
                    result = subprocess.run(
                        runas_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=15,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    return None
            else:
                # Tenta sem credenciais
                command = ['reg', 'query', f'\\\\{ip}\\HKLM\\SYSTEM\\CurrentControlSet\\Control\\Print\\Printers', '/s']
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            if result.returncode == 0:
                return WindowsPrinterManager._parse_registry_output(result.stdout, ip)
                
        except Exception as e:
            print(f"Registry query falhou para {ip}: {e}")
        
        return None
    
    @staticmethod
    def _parse_registry_output(output: str, ip: str) -> List[Dict[str, str]]:
        """Analisa a saída do registro para encontrar impressoras."""
        printers = []
        lines = output.split('\n')
        current_printer = None
        
        for line in lines:
            line = line.strip()
            if 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Print\\Printers\\' in line:
                # Nova impressora encontrada
                printer_name = line.split('\\')[-1]
                if printer_name and printer_name != 'Printers':
                    current_printer = {
                        'Name': printer_name,
                        'ShareName': printer_name,
                        'Status': 'Detectada via Registro',
                        'DriverName': f'Impressora {printer_name}',
                        'Location': f'Registro - {ip}',
                        'Comment': 'Encontrada no registro do sistema',
                        'IsDefault': 'FALSE'
                    }
            elif current_printer and 'Share' in line and 'REG_SZ' in line:
                # Verifica se é uma impressora compartilhada
                if current_printer not in printers:
                    printers.append(current_printer)
                current_printer = None
        
        return printers
    
    @staticmethod
    def _parse_net_view_output(output: str, ip: str) -> List[Dict[str, str]]:
        """Analisa a saída do comando NET VIEW."""
        printers = []
        lines = output.split('\n')
        
        # Procura por linhas que indicam impressoras
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['print', 'impressora', 'printer']):
                # Extrai o nome do compartilhamento
                parts = line.split()
                if parts:
                    share_name = parts[0]
                    # Remove caracteres especiais do início
                    share_name = share_name.strip('\\').strip()
                    
                    if share_name:
                        # Tenta obter mais informações sobre a impressora
                        printer_type = 'Impressora'
                        if len(parts) > 1:
                            description = ' '.join(parts[1:]).strip()
                            if description and description != 'Print':
                                printer_type = description
                        
                        printer_info = {
                            'Name': share_name,
                            'ShareName': share_name,
                            'Status': 'Compartilhada',
                            'DriverName': printer_type,
                            'Location': f'Rede - {ip}',
                            'Comment': 'Detectada via NET VIEW',
                            'IsDefault': 'FALSE'
                        }
                        printers.append(printer_info)
        
        return printers
    
    @staticmethod
    def _parse_powershell_output(output: str) -> List[Dict[str, str]]:
        """Analisa a saída do PowerShell."""
        printers = []
        lines = output.strip().split('\n')
        
        if len(lines) < 2:  # Precisa ter pelo menos header + 1 linha
            return printers
        
        # Primeira linha é o header
        headers = [h.strip('"') for h in lines[0].split(',')]
        
        for line in lines[1:]:
            if not line.strip():
                continue
                
            values = [v.strip('"') for v in line.split(',')]
            if len(values) >= len(headers):
                printer_info = {}
                for i, header in enumerate(headers):
                    printer_info[header] = values[i] if i < len(values) else ''
                
                # Só adiciona se tem ShareName
                if printer_info.get('ShareName'):
                    printer_info['Status'] = 'Compartilhada'
                    printer_info['IsDefault'] = 'FALSE'
                    printers.append(printer_info)
        
        return printers
    
    @staticmethod
    def _parse_wmic_output(output: str) -> List[Dict[str, str]]:
        """Analisa a saída do comando WMIC."""
        lines = output.strip().split('\n')
        if len(lines) < 2:
            return []

        printers = []
        
        # Encontra a linha do cabeçalho (primeira linha não vazia)
        header_line = None
        for line in lines:
            if line.strip() and 'Node' in line:
                header_line = line
                break
        
        if not header_line:
            return []
        
        header_parts = [h.strip() for h in header_line.split(',')]
        
        try:
            # Mapeia os índices das colunas
            column_indices = {}
            for i, header in enumerate(header_parts):
                if 'Name' in header and 'Name' not in column_indices:
                    column_indices['Name'] = i
                elif 'ShareName' in header:
                    column_indices['ShareName'] = i
                elif 'Status' in header:
                    column_indices['Status'] = i
                elif 'DriverName' in header:
                    column_indices['DriverName'] = i
                elif 'Location' in header:
                    column_indices['Location'] = i
                elif 'Comment' in header:
                    column_indices['Comment'] = i
                elif 'Default' in header:
                    column_indices['Default'] = i
        except Exception:
            return []

        for line in lines:
            if not line.strip() or 'Node' in line:
                continue
                
            values = [v.strip() for v in line.split(',')]
            
            # Verifica se tem dados suficientes
            if len(values) <= max(column_indices.values()):
                continue
            
            try:
                share_name = values[column_indices.get('ShareName', -1)] if 'ShareName' in column_indices else ""
                
                # Só adiciona se for uma impressora compartilhada
                if share_name and share_name.strip():
                    printer_info = {
                        'Name': values[column_indices.get('Name', -1)] if 'Name' in column_indices else share_name,
                        'ShareName': share_name,
                        'Status': values[column_indices.get('Status', -1)] if 'Status' in column_indices else 'Desconhecido',
                        'DriverName': values[column_indices.get('DriverName', -1)] if 'DriverName' in column_indices else '',
                        'Location': values[column_indices.get('Location', -1)] if 'Location' in column_indices else '',
                        'Comment': values[column_indices.get('Comment', -1)] if 'Comment' in column_indices else '',
                        'IsDefault': values[column_indices.get('Default', -1)] if 'Default' in column_indices else 'FALSE'
                    }
                    printers.append(printer_info)
            except IndexError:
                continue
                
        return printers
    
    @staticmethod
    def get_printer_display_name(printer_info: Dict[str, str]) -> str:
        """Gera um nome de exibição amigável para a impressora."""
        name = printer_info.get('Name', '').strip()
        driver_name = printer_info.get('DriverName', '').strip()
        location = printer_info.get('Location', '').strip()
        share_name = printer_info.get('ShareName', '').strip()
        
        # Prioriza o nome do driver se disponível e mais descritivo
        if driver_name and len(driver_name) > len(name) and 'Impressora em' not in driver_name and driver_name != name:
            display_name = driver_name
        elif name and name != share_name:
            display_name = name
        elif share_name:
            display_name = share_name
        else:
            display_name = 'Impressora Desconhecida'
        
        # Adiciona localização se disponível e não for genérica
        if location and 'Rede -' not in location and 'Registro -' not in location and location.strip():
            display_name += f" ({location})"
            
        return display_name
    
    @staticmethod
    def install_network_printer(printer_path: str) -> bool:
        """Instala uma impressora de rede usando o assistente do Windows."""
        try:
            command = f'rundll32.exe printui.dll,PrintUIEntry /in /n "{printer_path}"'
            subprocess.run(command, shell=True)
            return True
        except Exception as e:
            print(f"Erro ao instalar impressora {printer_path}: {e}")
            return False


# Função de compatibilidade com o código existente
def get_windows_shared_printers(ip: str) -> Optional[List[Dict[str, str]]]:
    """
    Função de compatibilidade para manter a interface existente.
    
    Args:
        ip (str): Endereço IP do host
        
    Returns:
        List[Dict[str, str]] | None: Lista de impressoras compartilhadas
    """
    return WindowsPrinterManager.get_shared_printers(ip)