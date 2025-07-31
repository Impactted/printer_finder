# network_utils.py
import nmap
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
        nm.scan(ip, arguments='-sV -T4 -p 9100,631,515,139,445,80,443')
        
        if ip in nm.all_hosts() and nm[ip].state() == 'up':
            return nm[ip]
        return None
        
    except Exception as e:
        print(f"Erro no Nmap para o IP {ip}: {e}")
        return None


def detect_device_type(nmap_data: dict, ip: str) -> tuple[str, str]:
    """
    Detecta o tipo de dispositivo baseado nos dados do Nmap.
    
    Args:
        nmap_data (dict): Dados retornados pelo Nmap
        ip (str): Endereço IP do dispositivo
        
    Returns:
        tuple[str, str]: (tipo_dispositivo, status_display)
    """
    tcp_ports = nmap_data.get('tcp', {})
    
    # Verifica se é impressora de rede direta
    for port, info in tcp_ports.items():
        if (port in [9100, 631, 515] or 
            'jetdirect' in info.get('name', '').lower() or 
            'ipp' in info.get('name', '').lower()):
            
            product_name = info.get('product', 'Impressora de Rede')
            return 'network_printer', product_name
    
    # Verifica se é host Windows com compartilhamentos
    if 139 in tcp_ports or 445 in tcp_ports:
        shared_printers = get_windows_shared_printers(ip)
        if shared_printers:
            # Usa o nome da primeira impressora encontrada
            printer_name = shared_printers[0].get('DriverName') or shared_printers[0].get('Name', 'Impressora')
            return 'shared_printer', f"Compartilhando: {printer_name}"
    
    # Dispositivo ativo padrão
    return 'device', 'Ativo'


def get_device_vendor_info(nmap_data: dict) -> dict:
    """
    Extrai informações de fabricante do dispositivo.
    
    Args:
        nmap_data (dict): Dados do Nmap
        
    Returns:
        dict: Informações de fabricante e endereço MAC
    """
    return {
        'mac': nmap_data.get('addresses', {}).get('mac', '').upper(),
        'vendor': list(nmap_data.get('vendor', {}).values())[0] if nmap_data.get('vendor') else ''
    }