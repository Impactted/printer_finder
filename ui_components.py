# ui_components.py
import customtkinter as ctk
from tkinter import ttk

class CollapsibleFrame(ctk.CTkFrame):
    def __init__(self, parent, category_name: str, app):
        super().__init__(parent, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self.category_name = category_name
        self.item_count = 0
        self.is_collapsed = True
        
        self.header_button = ctk.CTkButton(
            self, text=f"▶ {self.category_name} (0)", anchor="w",
            font=app.font_header, command=self.toggle
        )
        self.header_button.grid(row=0, column=0, sticky="ew")
        
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(self.content_frame, 
                                columns=("IP", "Hostname", "MAC", "Status"), 
                                show="headings", height=8)
        
        col_widths = {"IP": 140, "Hostname": 200, "MAC": 140, "Status": 400}
        for col, width in col_widths.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="w")
        
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=5)

    def toggle(self):
        self.is_collapsed = not self.is_collapsed
        prefix = "▶" if self.is_collapsed else "▼"
        
        if self.is_collapsed:
            self.content_frame.grid_forget()
        else:
            self.content_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 0))
            
        self.header_button.configure(text=f"{prefix} {self.category_name} ({self.item_count})")

    def add_entry(self, values: tuple):
        self.tree.insert("", "end", values=values)
        self.item_count += 1
        prefix = "▼" if not self.is_collapsed else "▶"
        self.header_button.configure(text=f"{prefix} {self.category_name} ({self.item_count})")

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_count = 0
        self.is_collapsed = True
        self.content_frame.grid_forget()
        self.header_button.configure(text=f"▶ {self.category_name} (0)")


class DetailsWindow(ctk.CTkToplevel):
    def __init__(self, parent, device_data):
        super().__init__(parent)
        self.title(f"Detalhes de {device_data.get('ip', 'N/A')}")
        self.geometry("600x450")
        self.transient(parent)
        self.grab_set()

        textbox = ctk.CTkTextbox(self, wrap="word", font=("Consolas", 12))
        textbox.pack(expand=True, fill="both", padx=10, pady=10)
        
        details_text = self.format_details(device_data)
        textbox.insert("1.0", details_text)
        textbox.configure(state="disabled")

    def format_details(self, data):
        text = f"IP Address: {data.get('ip', 'N/A')}\n"
        text += f"Hostname:   {data.get('hostname', 'N/A')}\n"
        text += f"MAC Address: {data.get('mac', 'N/A')}\n"
        text += f"Fabricante: {data.get('vendor', 'N/A')}\n"
        text += f"Status:     {data.get('status', {}).get('state', 'N/A').capitalize()}\n"
        text += "-"*50 + "\n"
        
        if data.get('shared_printers'):
            text += "IMPRESSORAS COMPARTILHADAS (via WMI):\n"
            for printer in data['shared_printers']:
                text += f"  - Nome do Driver: {printer.get('Name', 'N/A')}\n"
                text += f"    Nome do Compartilhamento: {printer.get('ShareName', 'N/A')}\n"
                text += f"    Status do Dispositivo: {printer.get('Status', 'N/A')}\n"
            text += "-"*50 + "\n"

        if 'tcp' in data:
            text += "PORTAS E SERVIÇOS ABERTOS:\n"
            for port, info in data['tcp'].items():
                product = info.get('product', '')
                version = info.get('version', '')
                name = info.get('name', '')
                text += f"  - Porta {port}/{info['state']}: {name} ({product} {version})\n".strip()
            text += "-"*50 + "\n"

        return text