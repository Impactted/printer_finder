#SYNC TEST
# app.py
import threading
import ipaddress
import subprocess
import csv
import time
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
import customtkinter as ctk
from tkinter import ttk, messagebox, Menu

# Importações dos nossos módulos
from ui_components import CollapsibleFrame, DetailsWindow
from network_utils import get_nmap_scan_data, get_windows_shared_printers

class NetworkScannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Scanner de Rede v12 (Modular)")
        self.geometry("1200x800")
        self.minsize(1000, 600)
        
        self.font_title = ctk.CTkFont(size=24, weight="bold")
        self.font_header = ctk.CTkFont(size=16, weight="bold")
        
        self.setup_styles()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.setup_ui()
        
        self.queue = Queue()
        self.scanning = False
        self.cancel_flag = False
        self.device_details = {} 
        self.completed_count = 0
        self.ip_list = []

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#2a2d2e", rowheight=28)
        style.configure("Treeview.Heading", font=('Segoe UI', 11, 'bold'), background="#1a1a1a", foreground="white")
        style.map('Treeview', background=[('selected', '#0078d4')])
        style.configure("TProgressbar", thickness=20)
        style.configure("green.Horizontal.TProgressbar", background='#00B050')
        style.configure("red.Horizontal.TProgressbar", background='#C00000')

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkLabel(main_frame, text="🔍 Scanner de Rede Inteligente", font=self.font_title)
        header.grid(row=0, column=0, columnspan=3, padx=15, pady=(10, 15))
        
        self.ip_entry = ctk.CTkEntry(main_frame, placeholder_text="Ex: 192.168.0.1 ou 192.168.0.1-255", height=35)
        self.ip_entry.grid(row=1, column=0, columnspan=3, padx=15, pady=(0, 10), sticky="ew")
        
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.scan_button = ctk.CTkButton(button_frame, text="🚀 Iniciar Scan", command=self.start_scan)
        self.scan_button.pack(side="left", padx=15)
        self.cancel_button = ctk.CTkButton(button_frame, text="⏹️ Cancelar", command=self.cancel_scan, state="disabled")
        self.cancel_button.pack(side="left")
        self.export_button = ctk.CTkButton(button_frame, text="📁 Exportar CSV", command=self.export_csv, state="disabled")
        self.export_button.pack(side="right", padx=15)
        
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=3, padx=15, pady=15, sticky="ew")
        self.status_label = ctk.CTkLabel(main_frame, text="Pronto para iniciar.", anchor="w")
        self.status_label.grid(row=4, column=0, columnspan=3, padx=15, sticky="ew")
        
        results_container = ctk.CTkScrollableFrame(self, label_text="📊 Resultados do Scan")
        results_container.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        results_container.grid_columnconfigure(0, weight=1)
        
        self.collapsible_frames = {}
        self.data_to_export = {}
        categories = ["🖨️ Impressoras Encontradas", "💻 Dispositivos Ativos"]
        
        for cat in categories:
            self.data_to_export[cat] = []
            frame = CollapsibleFrame(results_container, cat, self)
            frame.pack(fill="x", expand=True, padx=8, pady=3)
            self.collapsible_frames[cat] = frame
            frame.tree.bind("<Double-1>", self.show_details_window)
            frame.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        tree = event.widget
        item_id = tree.identify_row(event.y)
        if not item_id: return
        tree.selection_set(item_id)
        values = tree.item(item_id, 'values')
        ip = values[0]
        device_data = self.device_details.get(ip)
        if not device_data: return

        context_menu = Menu(tree, tearoff=0)
        context_menu.add_command(label="Ver Detalhes", command=lambda: self.open_details_for_ip(ip))
        context_menu.add_separator()
        context_menu.add_command(label=f"Copiar IP ({ip})", command=lambda: self.copy_to_clipboard(ip))
        if device_data.get('mac'):
            context_menu.add_command(label=f"Copiar MAC ({device_data['mac']})", command=lambda: self.copy_to_clipboard(device_data['mac']))
        
        if device_data.get('type') == 'shared_printer' and device_data.get('shared_printers'):
            context_menu.add_separator()
            for printer in device_data['shared_printers']:
                share_name = printer.get('ShareName')
                full_path = f"\\\\{ip}\\{share_name}"
                context_menu.add_command(label=f"Instalar Impressora '{share_name}'", 
                                          command=lambda p=full_path: self.install_printer(p))
        context_menu.post(event.x_root, event.y_root)

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_label.configure(text=f"'{text}' copiado para a área de transferência.")

    def install_printer(self, printer_path):
        try:
            command = f'rundll32.exe printui.dll,PrintUIEntry /in /n "{printer_path}"'
            messagebox.showinfo("Instalar Impressora",
                                f"Iniciando o assistente de instalação para:\n{printer_path}\n\n"
                                "Siga as instruções na tela do Windows.")
            subprocess.run(command, shell=True)
        except Exception as e:
            messagebox.showerror("Erro ao Instalar", f"Não foi possível iniciar o assistente.\nErro: {e}")

    def show_details_window(self, event):
        tree = event.widget
        selection = tree.selection()
        if not selection: return
        item_id = selection[0]
        ip = tree.item(item_id, 'values')[0]
        self.open_details_for_ip(ip)

    def open_details_for_ip(self, ip):
        device_data = self.device_details.get(ip)
        if device_data:
            DetailsWindow(self, device_data)

    def clear_results(self):
        self.progress['value'] = 0
        self.progress.configure(style="default.Horizontal.TProgressbar")
        self.status_label.configure(text="Pronto para iniciar.")
        self.export_button.configure(state="disabled")
        self.device_details.clear()
        for frame in self.collapsible_frames.values():
            frame.clear()
        for data_list in self.data_to_export.values():
            data_list.clear()

    def start_scan(self):
        if self.scanning: return
        ip_range_str = self.ip_entry.get().strip()
        if not ip_range_str:
            messagebox.showerror("Erro", "Por favor, digite um IP ou intervalo de IPs.")
            return
        
        try:
            if "-" in ip_range_str:
                parts = ip_range_str.split("-")
                if len(parts) != 2: raise ValueError("Formato de intervalo incorreto.")
                
                start_ip_str = parts[0].strip()
                end_ip_str = parts[1].strip()

                start_ip = ipaddress.IPv4Address(start_ip_str)
                if len(end_ip_str.split('.')) == 1:
                    end_ip_str = ".".join(start_ip_str.split('.')[:-1] + [end_ip_str])
                
                end_ip = ipaddress.IPv4Address(end_ip_str)

                if end_ip < start_ip:
                    messagebox.showerror("Erro de Intervalo", "O IP final do intervalo deve ser maior que o IP inicial.")
                    return
                self.ip_list = [str(ipaddress.IPv4Address(ip)) for ip in range(int(start_ip), int(end_ip) + 1)]
            else:
                self.ip_list = [str(ipaddress.IPv4Address(ip_range_str))]
        except ValueError as e:
            messagebox.showerror("Erro de Formato", f"Formato de IP ou intervalo inválido: {e}\nUse '192.168.0.1' ou '192.168.0.1-255'.")
            return
        
        self.clear_results()
        self.scanning = True
        self.cancel_flag = False
        self.completed_count = 0
        self.scan_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        threading.Thread(target=self.run_scan_in_parallel, daemon=True).start()
        self.after(100, self.update_progress)
        self.after(100, self.process_queue)

    def cancel_scan(self):
        if self.scanning:
            self.cancel_flag = True
            self.status_label.configure(text="Cancelando scan...")
            self.cancel_button.configure(state="disabled")

    def run_scan_in_parallel(self):
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ip = {executor.submit(self.scan_single_ip, ip): ip for ip in self.ip_list}
            for future in as_completed(future_to_ip):
                if self.cancel_flag: break
                try:
                    result = future.result()
                    if result: self.queue.put(("result", result))
                except Exception as e: print(f"Erro ao processar o futuro: {e}")
                finally: self.completed_count += 1
        self.queue.put(("done", "Scan cancelado." if self.cancel_flag else "Scan finalizado!"))

    def update_progress(self):
        if self.scanning:
            total_ips = len(self.ip_list)
            progress_pct = (self.completed_count / total_ips) * 100 if total_ips > 0 else 0
            self.progress['value'] = progress_pct
            self.status_label.configure(text=f"🔍 Escaneando... {self.completed_count}/{total_ips} IPs verificados.")
            self.after(200, self.update_progress)

    def scan_single_ip(self, ip: str) -> dict | None:
        if self.cancel_flag: return None
        nmap_data = get_nmap_scan_data(ip)
        if not nmap_data:
            return None 

        full_data = {
            'ip': ip,
            'hostname': nmap_data.get('hostnames', [{}])[0].get('name', ''),
            'mac': nmap_data.get('addresses', {}).get('mac', '').upper(),
            'vendor': list(nmap_data.get('vendor', {}).values())[0] if nmap_data.get('vendor') else '',
            'status': nmap_data.get('status', {}),
            'tcp': nmap_data.get('tcp', {}),
            'type': 'device',
            'simple_status': 'Ativo',
            'shared_printers': []
        }

        is_printer = False
        # 1. Procura por impressoras de rede diretas
        for port, info in full_data['tcp'].items():
            if port in [9100, 631, 515] or 'jetdirect' in info.get('name', '') or 'ipp' in info.get('name', ''):
                is_printer = True
                full_data['type'] = 'network_printer'
                product_name = info.get('product', 'Impressora de Rede')
                full_data['simple_status'] = product_name
                break
        
        # 2. Se não for, verifica se é um host de compartilhamento Windows
        if not is_printer and (139 in full_data['tcp'] or 445 in full_data['tcp']):
            shared_printers = get_windows_shared_printers(ip)
            if shared_printers:
                is_printer = True
                full_data['type'] = 'shared_printer'
                full_data['shared_printers'] = shared_printers
                printer_name = shared_printers[0].get('Name', 'Impressora Compartilhada')
                full_data['simple_status'] = f"Compartilhando: {printer_name}"

        return {"is_printer": is_printer, "data": full_data}

    def process_queue(self):
        try:
            msg_type, data = self.queue.get_nowait()
            if msg_type == "result":
                is_printer = data['is_printer']
                device_data = data['data']
                ip = device_data['ip']
                
                self.device_details[ip] = device_data

                values_active = (ip, device_data['hostname'], device_data['mac'], device_data['simple_status'])
                self.collapsible_frames["💻 Dispositivos Ativos"].add_entry(values_active)
                self.data_to_export["💻 Dispositivos Ativos"].append(values_active)

                if is_printer:
                    values_printer = (ip, device_data['hostname'], device_data['mac'], device_data['simple_status'])
                    self.collapsible_frames["🖨️ Impressoras Encontradas"].add_entry(values_printer)
                    self.data_to_export["🖨️ Impressoras Encontradas"].append(values_printer)

            elif msg_type == "done":
                self.scanning = False
                self.status_label.configure(text=data)
                self.scan_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
                self.progress['value'] = 100
                if "cancelado" in data.lower():
                    self.progress.configure(style="red.Horizontal.TProgressbar")
                else:
                    self.progress.configure(style="green.Horizontal.TProgressbar")
                if any(self.data_to_export.values()):
                    self.export_button.configure(state="normal")
                return
        except Empty:
            pass
        if self.scanning:
            self.after(50, self.process_queue)
            
    def export_csv(self):
        if not any(self.data_to_export.values()): return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Salvar resultados do scan")
        if not filepath: return
        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Categoria", "IP", "Hostname", "MAC", "Status"])
                for category, entries in self.data_to_export.items():
                    for entry in entries: writer.writerow([category] + list(entry))
            messagebox.showinfo("Exportação Concluída", f"Arquivo salvo em:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro na Exportação", f"Não foi possível salvar:\n{e}")