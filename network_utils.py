# network_utils.py
import nmap
import socket
import subprocess
import platform
from printer_utils import get_windows_shared_printers


def get_nmap_scan_data(ip: str) -> dict | None:
    """
    Usa o Nmap para escanear um IP e obter informações de rede.
    
    Args:
        ip (str): Endereço IP para escanear
        
    Returns:
        dict | None: Dados do scan ou None se o host não estiver ativo
    """
    try:
        nm = nmap.PortScanner() 
        # Scanning mais abrangente para melhor detecção
        nm.scan(ip, arguments='-sV -sS -O --osscan-guess -T4 -p 9100,631,515,139,445,80,443,21,22,23,25,53,110,143,993,995')
        
        if ip in nm.all_hosts() and nm[ip].state() == 'up':
            return nm[ip]
        return None
        
    except Exception as e:
        print(f"Erro no Nmap para o IP {ip}: {e}")
        return None


def get_hostname_advanced(ip: str, nmap_data: dict = None) -> str:
    """
    Obtém o hostname usando múltiplos métodos para maior precisão.
    
    Args:
        ip (str): Endereço IP
        nmap_data (dict): Dados do Nmap (opcional)
        
    Returns:
        str: Hostname encontrado ou string vazia
    """
    hostname = ""
    
    # Método 1: Usar dados do Nmap se disponível
    if nmap_data and nmap_data.get('hostnames'):
        for host_info in nmap_data['hostnames']:
            if host_info.get('name') and host_info['name'] != ip:
                hostname = host_info['name']
                break
    
    # Método 2: Resolução DNS reversa nativa do Python
    if not hostname:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror, OSError):
            pass
    
    # Método 3: nslookup do sistema
    if not hostname:
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['nslookup', ip], 
                                      capture_output=True, text=True, timeout=5,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Name:' in line:
                            hostname = line.split('Name:')[1].strip()
                            break
        except Exception:
            pass
    
    # Método 4: ping com resolução de nome (Windows)
    if not hostname and platform.system() == "Windows":
        try:
            result = subprocess.run(['ping', '-a', '-n', '1', ip], 
                                  capture_output=True, text=True, timeout=8,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Pinging' in line and '[' in line and ']' in line:
                        # Extrai hostname do formato "Pinging hostname [ip]"
                        start = line.find('Pinging ') + 8
                        end = line.find(' [')
                        if start < end:
                            potential_hostname = line[start:end].strip()
                            if potential_hostname != ip and '.' in potential_hostname:
                                hostname = potential_hostname
                                break
        except Exception:
            pass
    
    # Método 5: NetBIOS name query (Windows)
    if not hostname and platform.system() == "Windows":
        try:
            result = subprocess.run(['nbtstat', '-A', ip], 
                                  capture_output=True, text=True, timeout=10,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    line = line.strip()
                    if '<00>' in line and 'UNIQUE' in line:
                        # Extrai nome NetBIOS
                        parts = line.split()
                        if parts:
                            potential_name = parts[0].strip()
                            if potential_name and potential_name != ip:
                                hostname = potential_name
                                break
        except Exception:
            pass
    
    return hostname


def detect_device_type(nmap_data: dict, ip: str) -> tuple[str, str]:
    """
    Detecta o tipo de dispositivo baseado nos dados do Nmap com análise melhorada.
    
    Args:
        nmap_data (dict): Dados retornados pelo Nmap
        ip (str): Endereço IP do dispositivo
        
    Returns:
        tuple[str, str]: (tipo_dispositivo, status_display)
    """
    tcp_ports = nmap_data.get('tcp', {})
    os_info = nmap_data.get('osmatch', [])
    
    # Análise de OS para melhor categorização
    os_type = ""
    if os_info:
        os_name = os_info[0].get('name', '').lower()
        if 'windows' in os_name:
            os_type = "Windows"
        elif 'linux' in os_name:
            os_type = "Linux"
        elif 'printer' in os_name or 'hp' in os_name or 'canon' in os_name:
            os_type = "Printer"
    
    # Verifica se é impressora de rede direta
    for port, info in tcp_ports.items():
        service_name = info.get('name', '').lower()
        product = info.get('product', '').lower()
        
        # Portas e serviços típicos de impressoras
        if (port in [9100, 631, 515] or 
            'jetdirect' in service_name or 
            'ipp' in service_name or
            'printer' in product or
            'hp' in product or
            'canon' in product or
            'epson' in product):
            
            # Tenta obter nome mais descritivo
            if info.get('product'):
                product_name = info['product']
                if info.get('version'):
                    product_name += f" {info['version']}"
                return 'network_printer', product_name
            else:
                return 'network_printer', 'Impressora de Rede'
    
    # Verifica se é host Windows com compartilhamentos
    if 139 in tcp_ports or 445 in tcp_ports:
        shared_printers = get_windows_shared_printers(ip)
        if shared_printers:
            # Usa informações mais detalhadas da primeira impressora
            printer_info = shared_printers[0]
            printer_name = (printer_info.get('DriverName') or 
                          printer_info.get('Name') or 
                          'Impressora Compartilhada')
            return 'shared_printer', f"Compartilhando: {printer_name}"
    
    # Análise de outros tipos de dispositivos
    device_indicators = {
        80: "Servidor Web",
        443: "Servidor Web (HTTPS)",
        21: "Servidor FTP",
        22: "Servidor SSH",
        23: "Servidor Telnet",
        25: "Servidor SMTP",
        53: "Servidor DNS",
        110: "Servidor POP3",
        143: "Servidor IMAP"
    }
    
    # Identifica tipo baseado em serviços principais
    for port, service_type in device_indicators.items():
        if port in tcp_ports and tcp_ports[port].get('state') == 'open':
            if os_type:
                return 'device', f"{service_type} ({os_type})"
            else:
                return 'device', service_type
    
    # Dispositivo ativo padrão com informação de OS se disponível
    if os_type:
        return 'device', f'Dispositivo {os_type}'
    else:
        return 'device', 'Dispositivo Ativo'


def get_device_vendor_info(nmap_data: dict) -> dict:
    """
    Extrai informações de fabricante do dispositivo com análise melhorada.
    
    Args:
        nmap_data (dict): Dados do Nmap
        
    Returns:
        dict: Informações de fabricante e endereço MAC
    """
    mac_address = nmap_data.get('addresses', {}).get('mac', '').upper()
    vendor = ""
    
    # Primeiro tenta obter vendor do Nmap
    if nmap_data.get('vendor'):
        vendor = list(nmap_data['vendor'].values())[0]
    
    # Se não encontrou vendor mas tem MAC, tenta identificar pelo OUI
    if not vendor and mac_address:
        vendor = identify_vendor_by_oui(mac_address)
    
    # Análise adicional baseada em serviços para dispositivos sem MAC
    if not vendor:
        tcp_ports = nmap_data.get('tcp', {})
        for port, info in tcp_ports.items():
            product = info.get('product', '').lower()
            if 'hp' in product:
                vendor = "Hewlett-Packard"
                break
            elif 'canon' in product:
                vendor = "Canon"
                break
            elif 'epson' in product:
                vendor = "Epson"
                break
            elif 'brother' in product:
                vendor = "Brother"
                break
            elif 'microsoft' in product:
                vendor = "Microsoft"
                break
    
    return {
        'mac': mac_address,
        'vendor': vendor
    }


def identify_vendor_by_oui(mac_address: str) -> str:
    """
    Identifica o fabricante pelo OUI (Organizationally Unique Identifier).
    
    Args:
        mac_address (str): Endereço MAC
        
    Returns:
        str: Nome do fabricante ou string vazia
    """
    if not mac_address or len(mac_address) < 8:
        return ""
    
    # Extrai os primeiros 6 caracteres (3 bytes) do MAC
    oui = mac_address.replace(":", "").replace("-", "")[:6].upper()
    
    # Alguns OUIs comuns (você pode expandir esta lista)
    oui_database = {
        "001B63": "Hewlett-Packard",
        "0004AC": "Hewlett-Packard", 
        "0019BB": "Hewlett-Packard",
        "0023AE": "Hewlett-Packard",
        "002264": "Hewlett-Packard",
        "F4CE46": "Hewlett-Packard",
        "3C52F5": "Hewlett-Packard",
        "00A0D1": "Canon",
        "002115": "Canon",
        "8C2DAA": "Canon",
        "00908F": "Epson",
        "008094": "Epson",
        "00C048": "Brother",
        "002586": "Brother",
        "00E052": "Brother",
        "000D93": "Apple",
        "001EC9": "Apple",
        "ACFDEC": "Apple",
        "002522": "Apple",
        "0C7438": "Apple",
        "000C29": "VMware",
        "005056": "VMware",
        "000569": "VMware",
        "00155D": "Microsoft",
        "000BAB": "Microsoft",
        "0017FA": "Microsoft",
        "0050F2": "Microsoft",
        "3863BB": "Microsoft",
        "00E04C": "Realtek",
        "525400": "QEMU/KVM",
        "080027": "VirtualBox"
    }
    
    return oui_database.get(oui, "")


def ping_host(ip: str) -> bool:
    """
    Faz ping em um host para verificar conectividade básica.
    
    Args:
        ip (str): Endereço IP
        
    Returns:
        bool: True se o host responder ao ping
    """
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip], 
                                  capture_output=True, 
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                  capture_output=True)
        return result.returncode == 0
    except Exception:
        return False
