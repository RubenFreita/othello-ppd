import tkinter as tk
from tkinter import ttk

class ConnectionDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Conectar ao Servidor")
        
        # Define tamanho fixo da janela
        dialog_width = 400
        dialog_height = 180
        self.dialog.minsize(dialog_width, dialog_height)
        self.dialog.maxsize(dialog_width, dialog_height)
        
        # Torna a janela modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centraliza o diálogo
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Variáveis
        self.host = tk.StringVar(value="localhost")
        self.port = tk.StringVar(value="5000")
        self.result = None
        
        # Frame principal com padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configura o grid
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        
        # Widgets com tamanhos definidos
        ttk.Label(main_frame, text="Tipo de Conexão:").grid(row=0, column=0, sticky="w", pady=(0,5))
        self.connection_type = ttk.Combobox(main_frame, values=["Local", "Externa"], state="readonly")
        self.connection_type.set("Local")
        self.connection_type.grid(row=0, column=1, padx=(10,0), pady=(0,5))
        self.connection_type.bind('<<ComboboxSelected>>', self.on_connection_type_change)
        
        ttk.Label(main_frame, text="IP do Servidor:").grid(row=1, column=0, sticky="w", pady=(0,5))
        self.host_entry = ttk.Entry(main_frame, textvariable=self.host, width=25)
        self.host_entry.grid(row=1, column=1, padx=(10,0), pady=(0,5))
        
        ttk.Label(main_frame, text="Porta:").grid(row=2, column=0, sticky="w", pady=(0,15))
        entry_port = ttk.Entry(main_frame, textvariable=self.port, width=25)
        entry_port.grid(row=2, column=1, padx=(10,0), pady=(0,15))
        
        # Frame para botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2)
        
        # Botões com tamanhos definidos
        ttk.Button(btn_frame, text="Conectar", command=self.connect, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.cancel, width=15).pack(side=tk.LEFT, padx=5)
    
    def connect(self):
        self.result = (self.host.get(), int(self.port.get()))
        self.dialog.destroy()
    
    def cancel(self):
        self.dialog.destroy()
    
    def show(self):
        self.dialog.wait_window()
        return self.result
    
    def on_connection_type_change(self, event):
        if self.connection_type.get() == "Local":
            self.host.set("localhost")
        else:
            self.host.set("")  # Limpa o campo para digitar o IP público
