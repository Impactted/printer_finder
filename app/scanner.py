# app/scanner.py
import threading
import ipaddress
from queue import Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import messagebox

from network_utils import get_nmap_scan_data, detect_device_type, get_device_vendor_info
from printer_utils import get_windows_shared_printers, WindowsPrinterManager


class Scanner:
    def __init__(self, app):
        self.app = app
        
    def start_scan(self):
        """Inicia o processo de scanning."""
        if self.app.scanning:
            return
            
        ip_range_str = self.app.ui_manager.ip_entry.get().strip()
        if not ip_range_str:
            messagebox.showerror("Erro", "Por favor, digite um IP ou intervalo de IPs.")
            return
        
        try:
            self.app.ip_list = self._parse_ip_range(ip_range_str)
        except ValueError as e:
            messagebox.showerror("Erro de Formato", 
                               f"Formato de IP ou intervalo inválido: {e}\n"
                               "Use '192.168.0.1' ou '192.168.0.1-255'.")
            return
        
        self._initialize_scan()
        
    def _parse_ip_range(self, ip_range_str):
        """Converte string de IP/range em lista de IPs."""
        if "-" in ip_range_str:
            parts = ip_range_str.split("-")
            if len(parts) != 2:
                raise ValueError("Formato de intervalo incorreto.")
            
            start_ip_str = parts[0].strip()
            end_ip_str = parts[1].strip()

            start_ip = ipaddress.IPv4Address(start_ip_str)
            
            # Se o IP final for apenas o último octeto
            if len(end_ip_str.split('.')) == 1:
                end_ip_str = ".".join(start_ip_str.split('.')[:-1] + [end_ip_str])
            
            end_ip = ipaddress.IPv4Address(end_ip_str)

            if end_ip < start_ip:
                raise ValueError("O IP final do intervalo deve ser maior que o IP inicial.")
                
            return [str(ipaddress.IPv4Address(ip)) for ip in range(int(start_ip), int(end_ip) + 1)]
        else:
            return [str(ipaddress.IPv4Address(ip_range_str))]
            
    def _initialize_scan(self):
        """Inicializa as variáveis e inicia o thread de scanning."""
        self.app.ui_manager.clear_results()
        self.app.scanning = True
        self.app.cancel_flag = False
        self.app.completed_count = 0
        self.app.ui_manager.update_ui_state(scanning=True)
        
        threading.Thread(target=self.run_scan_in_parallel, daemon=True).start()
        self.app.after(100, self.update_progress)
        self.app.after(100, self.process_queue)

    def cancel_scan(self):
        """Cancela o scanning em andamento."""
        if self.app.scanning:
            self.app.cancel_flag = True
            self.app.ui_manager.status_label.configure(text="Cancelando scan...")
            self.app.ui_manager.cancel_button.configure(state="disabled")

    def run_scan_in_parallel(self):
        """Executa o scanning em paralelo usando ThreadPoolExecutor."""
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ip = {executor.submit(self.scan_single_ip, ip): ip 
                           for ip in self.app.ip_list}
            
            for future in as_completed(future_to_ip):
                if self.app.cancel_flag:
                    break
                try:
                    result = future.result()
                    if result:
                        self.app.queue.put(("result", result))
                except Exception as e:
                    print(f"Erro ao processar o futuro: {e}")
                finally:
                    self.app.completed_count += 1
                    
        completion_msg = "Scan cancelado." if self.app.cancel_flag else "Scan finalizado!"
        self.app.queue.put(("done", completion_msg))

    def update_progress(self):
        """Atualiza a barra de progresso."""
        if self.app.scanning:
            total_ips = len(self.app.ip_list)
            progress_pct = (self.app.completed_count / total_ips) * 100 if total_ips > 0 else 0
            self.app.ui_manager.progress['value'] = progress_pct
            self.app.ui_manager.status_label.configure(
                text=f"🔍 Escaneando... {self.app.completed_count}/{total_ips} IPs verificados."
            )
            self.app.after(200, self.update_progress)

    def scan_single_ip(self, ip: str):
        """Escaneia um único IP e retorna os dados encontrados."""
        if self.app.cancel_flag:
            return None
            
        nmap_data = get_nmap_scan_data(ip)
        if not nmap_data:
            return None

        # Obtém informações básicas do dispositivo
        vendor_info = get_device_vendor_info(nmap_data)
        device_type, status_display = detect_device_type(nmap_data, ip)
        
        full_data = {
            'ip': ip,
            'hostname': nmap_data.get('hostnames', [{}])[0].get('name', ''),
            'mac': vendor_info['mac'],
            'vendor': vendor_info['vendor'],
            'status': nmap_data.get('status', {}),
            'tcp': nmap_data.get('tcp', {}),
            'type': device_type,
            'simple_status': status_display,
            'shared_printers': []
        }

        # Se for impressora compartilhada, obtém detalhes das impressoras
        is_printer = device_type in ['network_printer', 'shared_printer']
        if device_type == 'shared_printer':
            shared_printers = get_windows_shared_printers(ip)
            if shared_printers:
                full_data['shared_printers'] = shared_printers
                # Atualiza o status com nome mais descritivo da primeira impressora
                printer_display = WindowsPrinterManager.get_printer_display_name(shared_printers[0])
                full_data['simple_status'] = f"Compartilhando: {printer_display}"

        return {"is_printer": is_printer, "data": full_data}



    def process_queue(self):
        """Processa a fila de resultados do scanning."""
        try:
            msg_type, data = self.app.queue.get_nowait()
            
            if msg_type == "result":
                self._process_scan_result(data)
            elif msg_type == "done":
                self._finalize_scan(data)
                return
                
        except Empty:
            pass
            
        if self.app.scanning:
            self.app.after(50, self.process_queue)
            
    def _process_scan_result(self, data):
        """Processa um resultado individual do scan."""
        is_printer = data['is_printer']
        device_data = data['data']
        ip = device_data['ip']
        
        self.app.device_details[ip] = device_data

        # Adiciona aos dispositivos ativos
        values_active = (ip, device_data['hostname'], device_data['mac'], device_data['simple_status'])
        self.app.ui_manager.collapsible_frames["💻 Dispositivos Ativos"].add_entry(values_active)
        self.app.ui_manager.data_to_export["💻 Dispositivos Ativos"].append(values_active)

        # Se for impressora, adiciona também à categoria de impressoras
        if is_printer:
            values_printer = (ip, device_data['hostname'], device_data['mac'], device_data['simple_status'])
            self.app.ui_manager.collapsible_frames["🖨️ Impressoras Encontradas"].add_entry(values_printer)
            self.app.ui_manager.data_to_export["🖨️ Impressoras Encontradas"].append(values_printer)

    def _finalize_scan(self, message):
        """Finaliza o processo de scanning."""
        self.app.scanning = False
        self.app.ui_manager.status_label.configure(text=message)
        self.app.ui_manager.update_ui_state(scanning=False)
        self.app.ui_manager.progress['value'] = 100
        
        if "cancelado" in message.lower():
            self.app.ui_manager.progress.configure(style="red.Horizontal.TProgressbar")
        else:
            self.app.ui_manager.progress.configure(style="green.Horizontal.TProgressbar")