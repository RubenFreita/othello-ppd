import tkinter as tk
from tkinter import ttk, messagebox
from server import OthelloServer
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
        
        # Label para IP (será atualizado quando o servidor iniciar)
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
        self.server = None
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
            self.server = OthelloServer(log_callback=self.log_message)
            # Atualiza o label com o IP
            self.ip_label.configure(
                text=f"IP para conexão: {self.server.network_ip} | Porta: {self.server.port}"
            )
            self.log_message(f"Servidor iniciado em {self.server.host}:{self.server.port}")
            self.server.start()
        except Exception as e:
            self.log_message(f"Erro ao iniciar servidor: {e}", "ERROR")

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja realmente encerrar o servidor?"):
            if self.server:
                self.server.stop()
            self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    server_gui = ServerGUI()
    server_gui.run()
