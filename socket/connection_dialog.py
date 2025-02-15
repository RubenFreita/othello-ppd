import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class ConnectionDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Conectar ao Servidor")
        
        # Define tamanho fixo da janela
        dialog_width = 300
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
        self.player_name = tk.StringVar(value="")
        self.result = None
        
        # Frame principal com padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configura o grid
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        
        # Widgets com tamanhos definidos
        ttk.Label(main_frame, text="IP do Servidor:").grid(row=0, column=0, sticky="w", pady=(0,5))
        entry_host = ttk.Entry(main_frame, textvariable=self.host, width=25)
        entry_host.grid(row=0, column=1, padx=(10,0), pady=(0,5))
        
        ttk.Label(main_frame, text="Seu Nome:").grid(row=1, column=0, sticky="w", pady=(0,5))
        entry_name = ttk.Entry(main_frame, textvariable=self.player_name, width=25)
        entry_name.grid(row=1, column=1, padx=(10,0), pady=(0,5))
        
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
        if not self.player_name.get().strip():
            messagebox.showerror("Erro", "Por favor, digite seu nome!")
            return
        self.result = (self.host.get(), int(self.port.get()), self.player_name.get().strip())
        self.dialog.destroy()
    
    def cancel(self):
        self.dialog.destroy()
    
    def show(self):
        self.dialog.wait_window()
        return self.result
