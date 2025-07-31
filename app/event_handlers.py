# app/event_handlers.py
import subprocess
import csv
from tkinter import messagebox, Menu, filedialog

from ui_components import DetailsWindow
from printer_utils import WindowsPrinterManager


class EventHandlers:
    def __init__(self, app):
        self.app = app
        
    def show_context_menu(self, event):
        """Mostra o menu de contexto ao clicar com botão direito."""
        tree = event.widget
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
            
        tree.selection_set(item_id)
        values = tree.item(item_id, 'values')
        ip = values[0]
        device_data = self.app.device_details.get(ip)
        if not device_data:
            return

        context_menu = Menu(tree, tearoff=0)
        context_menu.add_command(label="Ver Detalhes", 
                                command=lambda: self.open_details_for_ip(ip))
        context_menu.add_separator()
        context_menu.add_command(label=f"Copiar IP ({ip})", 
                                command=lambda: self.copy_to_clipboard(ip))
        
        if device_data.get('mac'):
            context_menu.add_command(label=f"Copiar MAC ({device_data['mac']})", 
                                    command=lambda: self.copy_to_clipboard(device_data['mac']))
        
        # Adiciona opções de impressora se aplicável
        self._add_printer_options(context_menu, device_data, ip)
        
        context_menu.post(event.x_root, event.y_root)

    def _add_printer_options(self, context_menu, device_data, ip):
        """Adiciona opções de impressora ao menu de contexto."""
        if (device_data.get('type') == 'shared_printer' and 
            device_data.get('shared_printers')):
            context_menu.add_separator()
            for printer in device_data['shared_printers']:
                share_name = printer.get('ShareName')
                full_path = f"\\\\{ip}\\{share_name}"
                context_menu.add_command(
                    label=f"Instalar Impressora '{share_name}'", 
                    command=lambda p=full_path: self.install_printer(p)
                )

    def copy_to_clipboard(self, text):
        """Copia texto para a área de transferência."""
        self.app.clipboard_clear()
        self.app.clipboard_append(text)
        self.app.ui_manager.status_label.configure(
            text=f"'{text}' copiado para a área de transferência."
        )

    def install_printer(self, printer_path):
        """Inicia o assistente de instalação de impressora."""
        try:
            success = WindowsPrinterManager.install_network_printer(printer_path)
            if success:
                messagebox.showinfo("Instalar Impressora",
                                   f"Iniciando o assistente de instalação para:\n{printer_path}\n\n"
                                   "Siga as instruções na tela do Windows.")
            else:
                messagebox.showerror("Erro ao Instalar", 
                                   "Não foi possível iniciar o assistente de instalação.")
        except Exception as e:
            messagebox.showerror("Erro ao Instalar", 
                               f"Não foi possível iniciar o assistente.\nErro: {e}")

    def show_details_window(self, event):
        """Mostra a janela de detalhes ao dar duplo clique."""
        tree = event.widget
        selection = tree.selection()
        if not selection:
            return
            
        item_id = selection[0]
        ip = tree.item(item_id, 'values')[0]
        self.open_details_for_ip(ip)

    def open_details_for_ip(self, ip):
        """Abre a janela de detalhes para um IP específico."""
        device_data = self.app.device_details.get(ip)
        if device_data:
            DetailsWindow(self.app, device_data)

    def export_csv(self):
        """Exporta os resultados para um arquivo CSV."""
        if not any(self.app.ui_manager.data_to_export.values()):
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Salvar resultados do scan"
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Categoria", "IP", "Hostname", "MAC", "Status"])
                
                for category, entries in self.app.ui_manager.data_to_export.items():
                    for entry in entries:
                        writer.writerow([category] + list(entry))
                        
            messagebox.showinfo("Exportação Concluída", 
                               f"Arquivo salvo em:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro na Exportação", 
                               f"Não foi possível salvar:\n{e}")