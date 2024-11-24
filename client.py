import tkinter as tk
from tkinter import messagebox
import socket
import json
import threading
from connection_dialog import ConnectionDialog

class OthelloClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Othello - Conectando...")
        
        self.board_size = 8
        self.cell_size = 60
        self.border_size = 40  # Tamanho da borda
        self.my_color = None
        self.current_turn = "black"
        self.game_active = False
        self.player_name = None
        
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        # Dimensões totais incluindo bordas
        self.total_width = self.board_size * self.cell_size + (2 * self.border_size)
        self.total_height = self.board_size * self.cell_size + (2 * self.border_size)
        
        # Frame principal para organizar tabuleiro e chat lado a lado
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10)
        
        # Frame para o tabuleiro
        self.board_frame = tk.Frame(self.main_frame)
        self.board_frame.pack(side=tk.LEFT)
        
        # Canvas do tabuleiro
        self.canvas = tk.Canvas(self.board_frame, width=self.total_width, height=self.total_height, bg="green")
        self.canvas.pack()
        
        # Frame para o chat com espaçamento
        self.chat_frame = tk.Frame(self.main_frame, padx=20)
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        
        # Título do chat com decoração
        self.chat_title_frame = tk.Frame(self.chat_frame, bg="#8B4513")
        self.chat_title_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Ícone do chat (emoji de conversa)
        self.chat_icon = tk.Label(self.chat_title_frame, text="💬", font=("Arial", 20), bg="#8B4513", fg="white")
        self.chat_icon.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Título do chat
        self.chat_title = tk.Label(self.chat_title_frame, text="Chat do Jogo", 
                                  font=("Arial", 14, "bold"), bg="#8B4513", fg="white")
        self.chat_title.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Área de mensagens com borda
        self.chat_area = tk.Text(self.chat_frame, width=30, height=20, state='disabled',
                                bd=2, relief="solid")
        self.chat_area.pack(pady=(0, 10))
        
        # Frame para entrada de mensagem
        self.message_frame = tk.Frame(self.chat_frame)
        self.message_frame.pack(fill=tk.X)
        
        # Campo de entrada de mensagem
        self.message_entry = tk.Entry(self.message_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Botão de enviar
        self.send_button = tk.Button(self.message_frame, text="Enviar", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Bind da tecla Enter para enviar mensagem
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.init_board()
        self.canvas.bind("<Button-1>", self.handle_click)
        
    def init_board(self):
        # Desenhar as bordas de madeira
        wood_color = "#8B4513"  # Cor marrom escuro para simular madeira
        
        # Borda superior
        self.canvas.create_rectangle(0, 0, self.total_width, self.border_size, fill=wood_color, outline=wood_color)
        # Borda inferior
        self.canvas.create_rectangle(0, self.total_height - self.border_size, self.total_width, self.total_height, fill=wood_color, outline=wood_color)
        # Borda esquerda
        self.canvas.create_rectangle(0, 0, self.border_size, self.total_height, fill=wood_color, outline=wood_color)
        # Borda direita
        self.canvas.create_rectangle(self.total_width - self.border_size, 0, self.total_width, self.total_height, fill=wood_color, outline=wood_color)

        # Desenha as letras (A-H) no topo e na base
        for col in range(self.board_size):
            letter = chr(65 + col)  # Converte número para letra (A=65 em ASCII)
            # Letras no topo
            self.canvas.create_text(
                self.border_size + col * self.cell_size + self.cell_size/2,
                self.border_size/2,
                text=letter,
                fill="white",
                font=("Arial", 14, "bold")
            )
            # Letras na base
            self.canvas.create_text(
                self.border_size + col * self.cell_size + self.cell_size/2,
                self.board_size * self.cell_size + self.border_size + self.border_size/2,
                text=letter,
                fill="white",
                font=("Arial", 14, "bold")
            )
        
        # Desenha os números (1-8) nas laterais
        for row in range(self.board_size):
            number = str(row + 1)
            # Números à esquerda
            self.canvas.create_text(
                self.border_size/2,
                self.border_size + row * self.cell_size + self.cell_size/2,
                text=number,
                fill="white",
                font=("Arial", 14, "bold")
            )
            # Números à direita
            self.canvas.create_text(
                self.board_size * self.cell_size + self.border_size + self.border_size/2,
                self.border_size + row * self.cell_size + self.cell_size/2,
                text=number,
                fill="white",
                font=("Arial", 14, "bold")
            )
        
        # Desenha o tabuleiro
        for row in range(self.board_size):
            for col in range(self.board_size):
                x1 = self.border_size + col * self.cell_size
                y1 = self.border_size + row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black")
        
        # Configuraão inicial das peças
        mid = self.board_size // 2
        self.place_piece(mid - 1, mid - 1, "white")
        self.place_piece(mid, mid, "white")
        self.place_piece(mid - 1, mid, "black")
        self.place_piece(mid, mid - 1, "black")
    
    def place_piece(self, row, col, color):
        x1 = self.border_size + col * self.cell_size + 5
        y1 = self.border_size + row * self.cell_size + 5
        x2 = self.border_size + (col + 1) * self.cell_size - 5
        y2 = self.border_size + (row + 1) * self.cell_size - 5
        self.board[row][col] = self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline=color)
    
    def handle_click(self, event):
        if not self.game_active or self.current_turn != self.my_color:
            return
            
        # Ajusta as coordenadas considerando a borda
        col = (event.x - self.border_size) // self.cell_size
        row = (event.y - self.border_size) // self.cell_size
        
        # Verifica se o clique foi dentro do tabuleiro
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            # Envia movimento para o servidor
            msg = {
                "type": "move",
                "row": row,
                "col": col
            }
            self.socket.send(json.dumps(msg).encode())
    
    def handle_remote_move(self, msg):
        if "no_valid_moves" in msg and msg["no_valid_moves"]:
            # Primeiro atualiza o turno
            self.current_turn = msg["next_turn"]
            self.update_status()
            
            # Processa a jogada
            row, col = msg["row"], msg["col"]
            color = msg["color"]
            
            # Coloca a nova peça
            self.place_piece(row, col, color)
            
            # Vira as peças
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            opponent_color = "white" if color == "black" else "black"
            
            for dr, dc in directions:
                pieces_to_flip = []
                r, c = row + dr, col + dc
                
                while 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if self.board[r][c] is None:
                        break
                    
                    current_color = self.canvas.itemcget(self.board[r][c], 'fill')
                    
                    if current_color == opponent_color:
                        pieces_to_flip.append((r, c))
                    elif current_color == color and pieces_to_flip:
                        for pr, pc in pieces_to_flip:
                            self.place_piece(pr, pc, color)
                        break
                    else:
                        break
                    
                    r += dr
                    c += dc
            
            # Mostra a mensagem depois de tudo processado
            messagebox.showinfo("Sem movimentos", 
                f"Jogador {opponent_color.capitalize()} não tem movimentos válidos. Passando a vez.")
            return
        
        row, col = msg["row"], msg["col"]
        color = msg["color"]
        
        # Coloca a nova peça
        self.place_piece(row, col, color)
        
        # Vira as peças
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        opponent_color = "white" if color == "black" else "black"
        
        for dr, dc in directions:
            pieces_to_flip = []
            r, c = row + dr, col + dc
            
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board[r][c] is None:
                    break
                
                current_color = self.canvas.itemcget(self.board[r][c], 'fill')
                
                if current_color == opponent_color:
                    pieces_to_flip.append((r, c))
                elif current_color == color and pieces_to_flip:
                    for pr, pc in pieces_to_flip:
                        self.place_piece(pr, pc, color)
                    break
                else:
                    break
                
                r += dr
                c += dc
        
        self.current_turn = msg["next_turn"]
        self.update_status()
    
    def update_status(self):
        # Conta as peças
        black_count = 0
        white_count = 0
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board[row][col] is not None:
                    color = self.canvas.itemcget(self.board[row][col], 'fill')
                    if color == "black":
                        black_count += 1
                    else:
                        white_count += 1
        
        # Atualiza o título com as informações
        status = f"Othello - Você é {self.my_color} | Turno: {self.current_turn} | B: {black_count} | W: {white_count}"
        if self.current_turn == self.my_color:
            status += " (Sua vez!)"
            self.canvas.configure(bg="green")
        else:
            self.canvas.configure(bg="darkgreen")
        
        self.root.title(status)
    
    def connect_to_server(self, host='localhost', port=5000, player_name="", game_id="game1"):
        try:
            # Armazena as informações de conexão
            self.host = host
            self.port = port
            self.player_name = player_name
            
            self.socket.connect((host, port))
            
            msg = {
                "type": "connect",
                "game_id": game_id,
                "player_name": player_name
            }
            self.socket.send(json.dumps(msg).encode())
            
            threading.Thread(target=self.receive_messages, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível conectar ao servidor: {e}")
    
    def receive_messages(self):
        buffer = ""
        while True:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                
                buffer += data
                
                try:
                    # Tenta processar o JSON do buffer
                    msg = json.loads(buffer)
                    buffer = ""  # Limpa o buffer após processar com sucesso
                    
                    if msg["type"] == "connected":
                        self.my_color = msg["color"]
                        self.root.after(0, self.update_status)
                    
                    elif msg["type"] == "game_start":
                        self.game_active = True
                        self.root.after(0, lambda: messagebox.showinfo("Jogo Iniciado", "O jogo começou!"))
                    
                    elif msg["type"] == "move":
                        self.root.after(0, lambda: self.handle_remote_move(msg))
                    
                    elif msg["type"] == "game_over":
                        self.root.after(0, lambda: self.handle_game_over(msg))
                    
                    elif msg["type"] == "chat":
                        self.root.after(0, lambda: self.display_message(msg["color"], msg["player_name"], msg["message"]))
                    
                except json.JSONDecodeError:
                    # Se não conseguir processar o JSON, mantém os dados no buffer
                    continue
                
            except Exception as e:
                print(f"Erro ao receber mensagem: {e}")
                break
    
    def handle_game_over(self, msg):
        winner = msg["winner"]
        black_count = msg["black_count"]
        white_count = msg["white_count"]
        
        if winner == "tie":
            message = f"Fim de jogo! Empate ({black_count} peças cada)!"
        else:
            message = f"Fim de jogo! {winner.capitalize()} vence ({black_count} vs {white_count})!"
        
        response = messagebox.askyesno(
            "Fim de Jogo",
            message + "\n\nDeseja jogar novamente?"
        )
        
        if response:
            self.reset_game()
        else:
            self.root.quit()
    
    def reset_game(self):
        # Guarda as informações de conexão atuais
        current_host = self.host if hasattr(self, 'host') else 'localhost'
        current_port = self.port if hasattr(self, 'port') else 5000
        current_name = self.player_name if self.player_name else "Jogador"
        
        # Fecha o socket antigo
        try:
            self.socket.close()
        except:
            pass
        
        # Cria um novo socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Limpa o tabuleiro
        self.canvas.delete("all")
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.current_turn = "black"
        self.game_active = False
        self.init_board()
        self.update_status()
        
        # Reconecta ao servidor usando as informações originais
        self.connect_to_server(host=current_host, port=current_port, player_name=current_name)
    
    def send_message(self):
        mensagem = self.message_entry.get().strip()
        if mensagem:
            msg = {
                "type": "chat",
                "color": self.my_color,
                "player_name": self.player_name,
                "message": mensagem
            }
            self.socket.send(json.dumps(msg).encode())
            self.message_entry.delete(0, tk.END)
    
    def display_message(self, color, player_name, mensagem):
        self.chat_area.configure(state='normal')
        
        if color == "system":
            tag = "system"
            name_color = "green"
        elif color == "black":
            tag = "black_player"
            name_color = "darkblue"
        else:
            tag = "white_player"
            name_color = "darkred"
        
        self.chat_area.tag_configure(tag, foreground=name_color)
        self.chat_area.insert(tk.END, f"{player_name}: ", tag)
        self.chat_area.insert(tk.END, f"{mensagem}\n")
        self.chat_area.see(tk.END)
        self.chat_area.configure(state='disabled')

def main():
    client = OthelloClient()
    
    # Mostra diálogo de conexão
    dialog = ConnectionDialog(client.root)
    connection_info = dialog.show()
    
    if connection_info:
        host, port, player_name = connection_info
        client.connect_to_server(host=host, port=port, player_name=player_name)
        client.root.mainloop()
    else:
        client.root.destroy()

if __name__ == "__main__":
    main()
