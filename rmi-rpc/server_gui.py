import tkinter as tk
from tkinter import ttk, messagebox
import Pyro4
import threading
import datetime

class ServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Servidor Othello")
        self.root.geometry("600x450")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para título e informações
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Título de boas-vindas
        welcome_label = ttk.Label(
            info_frame, 
            text="Bem vindo ao jogo de Othello",
            font=("Arial", 16, "bold")
        )
        welcome_label.pack(pady=(0, 5))
        
        # Label para IP
        self.ip_label = ttk.Label(
            info_frame, 
            text="Aguardando inicialização do servidor...",
            font=("Arial", 12)
        )
        self.ip_label.pack()
        
        # Área de logs
        log_frame = ttk.LabelFrame(main_frame, text="Logs do Servidor", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Text widget para logs com scrollbar
        self.log_area = tk.Text(log_frame, wrap=tk.WORD, height=20)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_area.yview)
        self.log_area.configure(yscrollcommand=scrollbar.set)
        
        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configurar o fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar servidor em uma thread separada
        self.daemon = None
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()

    def log_message(self, message, message_type="INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{message_type}] {message}\n"
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, log_entry)
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')
        self.root.update()

    def start_server(self):
        try:
            from server import OthelloServer
            server = OthelloServer(log_callback=self.log_message)
            self.daemon = Pyro4.Daemon(host='0.0.0.0', port=5000)
            uri = self.daemon.register(server, "othello.server")
            
            self.ip_label.configure(
                text=f"URI do servidor: {uri}"
            )
            self.log_message(f"Servidor iniciado com URI: {uri}")
            self.daemon.requestLoop()
        except Exception as e:
            self.log_message(f"Erro ao iniciar servidor: {e}", "ERROR")

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja realmente encerrar o servidor?"):
            if self.daemon:
                self.daemon.shutdown()
            self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    server_gui = ServerGUI()
    server_gui.run()
