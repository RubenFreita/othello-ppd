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
        
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        # Dimensões totais incluindo bordas
        total_width = self.board_size * self.cell_size + (2 * self.border_size)
        total_height = self.board_size * self.cell_size + (2 * self.border_size)
        
        # Criar canvas com as novas dimensões
        self.canvas = tk.Canvas(self.root, width=total_width, height=total_height, bg="green")
        self.canvas.pack(padx=10, pady=10)
        
        # Desenhar as bordas de madeira
        wood_color = "#8B4513"  # Cor marrom escuro para simular madeira
        
        # Borda superior
        self.canvas.create_rectangle(0, 0, total_width, self.border_size, fill=wood_color, outline=wood_color)
        # Borda inferior
        self.canvas.create_rectangle(0, total_height - self.border_size, total_width, total_height, fill=wood_color, outline=wood_color)
        # Borda esquerda
        self.canvas.create_rectangle(0, 0, self.border_size, total_height, fill=wood_color, outline=wood_color)
        # Borda direita
        self.canvas.create_rectangle(total_width - self.border_size, 0, total_width, total_height, fill=wood_color, outline=wood_color)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.init_board()
        self.canvas.bind("<Button-1>", self.handle_click)
        
    def init_board(self):
        # Desenha as letras (A-H) no topo e na base
        for col in range(self.board_size):
            letter = chr(65 + col)  # Converte número para letra (A=65 em ASCII)
            # Letras no topo
            self.canvas.create_text(
                self.border_size + col * self.cell_size + self.cell_size/2,
                self.border_size/2,
                text=letter,
                fill="white",
                font=("Arial", 12, "bold")
            )
            # Letras na base
            self.canvas.create_text(
                self.border_size + col * self.cell_size + self.cell_size/2,
                self.board_size * self.cell_size + self.border_size + self.border_size/2,
                text=letter,
                fill="white",
                font=("Arial", 12, "bold")
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
                font=("Arial", 12, "bold")
            )
            # Números à direita
            self.canvas.create_text(
                self.board_size * self.cell_size + self.border_size + self.border_size/2,
                self.border_size + row * self.cell_size + self.cell_size/2,
                text=number,
                fill="white",
                font=("Arial", 12, "bold")
            )
        
        # Desenha o tabuleiro
        for row in range(self.board_size):
            for col in range(self.board_size):
                x1 = self.border_size + col * self.cell_size
                y1 = self.border_size + row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black")
        
        # Configura��ão inicial das peças
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
            # Primeiro coloca a peça e vira as outras
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
            
            # Depois mostra a mensagem e atualiza o turno
            messagebox.showinfo("Sem movimentos", 
                f"Jogador {opponent_color.capitalize()} não tem movimentos válidos. Passando a vez.")
            self.current_turn = msg["next_turn"]
            self.update_status()
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
    
    def connect_to_server(self, host='localhost', port=5000, game_id="game1"):
        try:
            self.socket.connect((host, port))
            
            msg = {
                "type": "connect",
                "game_id": game_id
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
        
        # Reconecta ao servidor
        self.connect_to_server()

def main():
    client = OthelloClient()
    
    # Mostra diálogo de conexão
    dialog = ConnectionDialog(client.root)
    connection_info = dialog.show()
    
    if connection_info:
        host, port = connection_info
        client.connect_to_server(host=host, port=port)
        client.root.mainloop()
    else:
        client.root.destroy()

if __name__ == "__main__":
    main()
