import tkinter as tk
from tkinter import messagebox
import Pyro4
import threading
from connection_dialog import ConnectionDialog
import time
from tkinter import ttk

class OthelloClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Othello - Conectando...")
        
        self.board_size = 8
        self.cell_size = 60
        self.border_size = 40  # Tamanho da borda
        self.piece_padding = 5  # Padding padrão para todas as peças
        self.piece_size = self.cell_size - (2 * self.piece_padding)  # Tamanho padrão para todas as peças
        
        self.my_color = None
        self.current_turn = "black"
        self.game_active = False
        self.player_name = None
        self.game_id = "game1"
        
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
        
        # Frame para botões
        self.buttons_frame = tk.Frame(self.chat_frame)
        self.buttons_frame.pack(fill=tk.X, pady=5)
        
        # Botão de enviar
        self.send_button = ttk.Button(
            self.buttons_frame,
            text="Enviar",
            command=self.send_message
        )
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        # Botão de desistir
        self.surrender_button = ttk.Button(
            self.buttons_frame,
            text="Desistir",
            command=self.request_surrender
        )
        self.surrender_button.pack(side=tk.LEFT, padx=5)
        
        # Bind da tecla Enter para enviar mensagem
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Inicializa o tabuleiro e configura eventos
        self.init_board()
        self.canvas.bind("<Button-1>", self.handle_click)
        
        # Variável para armazenar a referência do servidor Pyro
        self.server = None
        
        # Thread para atualização do jogo
        self.update_thread = None
        self.running = True
        
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
        x_center = self.border_size + col * self.cell_size + (self.cell_size / 2)
        y_center = self.border_size + row * self.cell_size + (self.cell_size / 2)
        radius = self.piece_size / 2
        
        self.board[row][col] = self.canvas.create_oval(
            x_center - radius,
            y_center - radius,
            x_center + radius,
            y_center + radius,
            fill=color,
            outline="gray"
        )
    
    def handle_click(self, event):
        if not self.game_active or self.current_turn != self.my_color:
            return
            
        col = (event.x - self.border_size) // self.cell_size
        row = (event.y - self.border_size) // self.cell_size
        
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            try:
                response = self.server.make_move(self.game_id, self.player_name, row, col)
                
                if response["status"] == "success":
                    self.handle_remote_move(response)
                elif response["status"] == "game_over":
                    self.handle_game_over(response)
                elif response["status"] == "error":
                    messagebox.showerror("Erro", response["message"])
                    
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao fazer movimento: {e}")
    
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
            self._flip_pieces(row, col, color)
            
            # Mostra a mensagem depois de tudo processado
            messagebox.showinfo("Sem movimentos", 
                f"Jogador {self.current_turn.capitalize()} não tem movimentos válidos. Passando a vez.")
            return
        
        row, col = msg["row"], msg["col"]
        color = msg["color"]
        
        # Coloca a nova peça
        self.place_piece(row, col, color)
        
        # Vira as peças
        self._flip_pieces(row, col, color)
        
        self.current_turn = msg["next_turn"]
        self.update_status()
    
    def _flip_pieces(self, row, col, color):
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
    
    def connect_to_server(self, host='localhost', port=5000, player_name=""):
        try:
            uri = f"PYRO:othello.server@{host}:{port}"
            self.server = Pyro4.Proxy(uri)
            self.player_name = player_name
            self.host = host
            self.port = port
            
            # Tenta conectar ao jogo
            response = self.server.connect_player(player_name, self.game_id)
            
            if response["status"] == "connected":
                self.my_color = response["color"]
                self.game_active = response["game_started"]
                self.update_status()
                
                if response["game_started"]:
                    messagebox.showinfo("Jogo Iniciado", "O jogo começou!")
                
                # Inicia thread de atualização
                self.update_thread = threading.Thread(target=self.update_game_state, daemon=True)
                self.update_thread.start()
                
                return True
            else:
                messagebox.showerror("Erro", response["message"])
                return False
                
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível conectar ao servidor: {e}")
            return False
    
    def update_game_state(self):
        while self.running:
            try:
                response = self.server.get_game_state(self.game_id, self.player_name)
                
                if response["status"] == "success":
                    if response["type"] == "surrender_request":
                        # Para a thread temporariamente
                        self.running = False
                        # Mostra o diálogo de desistência
                        requester = response["requester"]
                        self.root.after(0, lambda: self.handle_surrender_request(requester))
                        break
                    
                    elif response["type"] == "surrender_cancelled":
                        print(self.player_name)
                        print(response.get("requester"))
                        print("aaaaaaaaaaaaaaaaaaaaaa")
                        # Mostra mensagem para quem pediu a desistência
                        if self.player_name == response.get("requester"):
                            messagebox.showinfo("Desistência Recusada", 
                                "Sua solicitação de desistência foi recusada. O jogo continua!")
                            self.running = True
                            self.update_thread = threading.Thread(target=self.update_game_state, daemon=True)
                            self.update_thread.start()
                            break
                    
                    elif response["type"] == "game_over_surrender":
                        # Caso especial para fim de jogo por desistência
                        surrendered_by = response["surrendered_by"]
                        winner = response["winner"]
                        message = f"Fim de jogo! {surrendered_by} desistiu. {winner} vence!"
                        self.running = False
                        messagebox.showinfo("Fim de Jogo", message)
                        self.root.quit()
                        break
                    
                    elif response["type"] == "game_started":
                        self.game_active = True
                        messagebox.showinfo("Jogo Iniciado", "O jogo começou!")
                    elif response["type"] == "game_state":
                        self.update_board_from_state(response["board"])
                        self.current_turn = response["current_turn"]
                        self.update_status()
                        
                        # Processa mensagens de chat não lidas
                        if "chat_messages" in response:
                            for msg in response["chat_messages"]:
                                self.display_message(msg["color"], msg["player_name"], msg["message"])
                    elif response["type"] == "chat":
                        self.display_message(response["color"], response["player_name"], response["message"])
                    
                    elif response["type"] == "no_valid_moves":
                        self.current_turn = response["current_turn"]
                        self.update_status()
                        messagebox.showinfo("Sem movimentos", 
                            f"Jogador {self.current_turn.capitalize()} não tem movimentos válidos. Passando a vez.")
                    elif response["type"] == "game_over":
                        # Primeiro atualiza o tabuleiro
                        self.update_board_from_state(response["board"])
                        self.update_status()
                        # Depois mostra a mensagem de fim de jogo
                        self.handle_game_over(response)
                        break
                    
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Erro na atualização do estado do jogo: {e}")
                time.sleep(1)
    
    def update_board_from_state(self, board_state):
        for row in range(self.board_size):
            for col in range(self.board_size):
                current_piece = board_state[row][col]
                current_canvas_piece = self.board[row][col]
                
                if current_piece is not None:
                    # Se não existe peça no canvas nesta posição, cria uma nova
                    if current_canvas_piece is None:
                        x_center = self.border_size + col * self.cell_size + (self.cell_size / 2)
                        y_center = self.border_size + row * self.cell_size + (self.cell_size / 2)
                        radius = self.piece_size / 2
                        
                        piece = self.canvas.create_oval(
                            x_center - radius,
                            y_center - radius,
                            x_center + radius,
                            y_center + radius,
                            fill=current_piece,
                            outline="gray"
                        )
                        self.board[row][col] = piece
                    else:
                        # Se já existe uma peça, apenas atualiza sua cor
                        self.canvas.itemconfig(current_canvas_piece, fill=current_piece)
                elif current_canvas_piece is not None:
                    # Se existe uma peça no canvas mas não deveria existir, remove-a
                    self.canvas.delete(current_canvas_piece)
                    self.board[row][col] = None
    
    def handle_game_over(self, msg):
        # Primeiro atualiza o tabuleiro com o estado final
        if "board" in msg:
            self.update_board_from_state(msg["board"])
    
        winner = msg["winner"]
        
        # Verifica se é um fim de jogo por desistência
        if msg.get("surrender"):
            surrendered_by = msg.get("surrendered_by", "Oponente")
            message = f"Fim de jogo! {surrendered_by} desistiu. {winner.capitalize()} vence!"
            messagebox.showinfo("Fim de Jogo", message)
            self.root.quit()
            return
        
        # Caso normal de fim de jogo
        black_count = msg["black_count"]
        white_count = msg["white_count"]
        
        if winner == "tie":
            message = f"Fim de jogo! Empate ({black_count} peças cada)!"
        else:
            message = f"Fim de jogo! {winner.capitalize()} vence ({black_count} vs {white_count})!"
        
        # Para a thread de atualização
        self.running = False
        
        # Usa after para garantir que a mensagem apareça após a atualização da UI
        self.root.after(100, lambda: self._show_game_over_dialog(message))

    def _show_game_over_dialog(self, message):
        response = messagebox.askyesno(
            "Fim de Jogo",
            message + "\n\nDeseja jogar novamente?"
        )
        
        if response:
            self.reset_game()
        else:
            self.root.quit()
    
    def reset_game(self):
        try:
            # Primeiro tenta reiniciar o jogo no servidor
            response = self.server.reset_game(self.game_id)
            if response["status"] == "success":
                # Limpa o tabuleiro local
                self.canvas.delete("all")
                self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
                self.current_turn = "black"
                self.game_active = True
                self.init_board()
                self.update_status()
                
                # Limpa o chat
                self.chat_area.configure(state='normal')
                self.chat_area.delete(1.0, tk.END)
                self.chat_area.configure(state='disabled')
                
                # Reinicia a thread de atualização
                self.running = True
                self.update_thread = threading.Thread(target=self.update_game_state, daemon=True)
                self.update_thread.start()
            else:
                messagebox.showerror("Erro", response["message"])
                self.root.quit()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao reiniciar o jogo: {e}")
            self.root.quit()
    
    def send_message(self):
        mensagem = self.message_entry.get().strip()
        if mensagem:
            try:
                response = self.server.send_chat_message(self.game_id, self.player_name, mensagem)
                if response["status"] == "success":
                    self.message_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao enviar mensagem: {e}")
    
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

    def __del__(self):
        self.running = False
        if self.update_thread:
            self.update_thread.join()

    def request_surrender(self):
        if not self.game_active:
            return
        
        response = messagebox.askyesno(
            "Confirmar Desistência",
            "Você realmente deseja desistir da partida?"
        )
        
        if response:
            try:
                result = self.server.request_surrender(self.game_id, self.player_name)
                if result["status"] == "error":
                    messagebox.showerror("Erro", result["message"])
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao solicitar desistência: {e}")

    def handle_surrender_request(self, opponent_name):
        response = messagebox.askyesno(
            "Solicitação de Desistência",
            f"{opponent_name} deseja desistir da partida.\nVocê aceita a desistência e vence o jogo?"
        )
        
        try:
            result = self.server.respond_to_surrender(self.game_id, self.player_name, response)
            if result["status"] == "success":
                if response:
                    # Mostra mensagem de vitória por desistência
                    message = f"Você aceitou a desistência de {opponent_name} e venceu o jogo!"
                    messagebox.showinfo("Vitória por Desistência", message)
                    self.root.quit()
                else:
                    # Se recusou a desistência, reinicia a thread de atualização
                    self.running = True
                    self.update_thread = threading.Thread(target=self.update_game_state, daemon=True)
                    self.update_thread.start()
            else:
                messagebox.showerror("Erro", result["message"])
                # Reinicia a thread em caso de erro
                self.running = True
                self.update_thread = threading.Thread(target=self.update_game_state, daemon=True)
                self.update_thread.start()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao responder à desistência: {e}")
            # Reinicia a thread em caso de erro
            self.running = True
            self.update_thread = threading.Thread(target=self.update_game_state, daemon=True)
            self.update_thread.start()

def main():
    client = OthelloClient()
    
    # Mostra diálogo de conexão
    dialog = ConnectionDialog(client.root)
    connection_info = dialog.show()
    
    if connection_info:
        host, port, player_name = connection_info
        if client.connect_to_server(host=host, port=port, player_name=player_name):
            client.root.mainloop()
    else:
        client.root.destroy()

if __name__ == "__main__":
    main()
