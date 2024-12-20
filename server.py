import socket
import threading
import json
from game_logic import OthelloGame
import time

class OthelloServer:
    def __init__(self, host='0.0.0.0', port=5000, log_callback=None):
        self.host = host
        self.port = port
        self.log_callback = log_callback
        self.running = True
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(2)
        
        self.games = {}
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.network_ip = s.getsockname()[0]
            s.close()
        except:
            self.network_ip = socket.gethostbyname(socket.gethostname())

    def log(self, message, message_type="INFO"):
        if self.log_callback:
            self.log_callback(message, message_type)
        else:
            print(f"[{message_type}] {message}")

    def start(self):
        while self.running:
            try:
                client_socket, address = self.server.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, address)).start()
            except:
                if self.running:
                    self.log("Erro ao aceitar conexão", "ERROR")
                break

    def handle_client(self, client_socket, address):
        try:
            data = client_socket.recv(1024).decode()
            msg = json.loads(data)
            
            if msg["type"] == "connect":
                player_name = msg.get("player_name", "Jogador")
                self.log(f"Jogador '{player_name}' conectou-se ao servidor")
                game_id = msg.get("game_id", "game1")
                
                if game_id not in self.games:
                    self.games[game_id] = {
                        "game": OthelloGame(),
                        "players": [],
                        "current_turn": "black"
                    }
                
                game_data = self.games[game_id]
                
                if len(game_data["players"]) < 2:
                    # Atribui cor ao jogador
                    color = "black" if not game_data["players"] else "white"
                    
                    # Adiciona o jogador ao jogo
                    game_data["players"].append({
                        "socket": client_socket,
                        "color": color,
                        "name": player_name
                    })
                    
                    # Envia confirmação de conexão
                    connect_msg = {
                        "type": "connected",
                        "color": color
                    }
                    client_socket.send(json.dumps(connect_msg).encode())
                    
                    # Se dois jogadores conectados, inicia o jogo
                    if len(game_data["players"]) == 2:
                        self.broadcast_game_start(game_id)
                    
                    # Inicia thread para processar mensagens do cliente
                    threading.Thread(target=self.handle_game_messages, 
                                   args=(game_id, client_socket),
                                   daemon=True).start()
            
        except Exception as e:
            print(f"Erro ao processar conexão: {e}")
            self.remove_client(client_socket)
    
    def handle_game_messages(self, game_id, client_socket):
        game_data = self.games[game_id]
        game = game_data["game"]
        
        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                
                msg = json.loads(data)
                
                if msg["type"] == "move":
                    player = next(p for p in game_data["players"] if p["socket"] == client_socket)
                    
                    if player["color"] == game_data["current_turn"]:
                        row, col = msg["row"], msg["col"]
                        
                        if game.is_valid_move(row, col, player["color"]):
                            # Faz o movimento
                            game.make_move(row, col, player["color"])
                            next_color = "white" if player["color"] == "black" else "black"
                            
                            # Envia o movimento para todos
                            move_msg = {
                                "type": "move",
                                "row": row,
                                "col": col,
                                "color": player["color"],
                                "next_turn": next_color
                            }
                            self.broadcast_to_game(game_id, move_msg)
                            
                            # Verifica movimentos válidos para o próximo jogador
                            has_valid_moves = False
                            for r in range(game.board_size):
                                for c in range(game.board_size):
                                    if game.board[r][c] is None and game.is_valid_move(r, c, next_color):
                                        has_valid_moves = True
                                        break
                                if has_valid_moves:
                                    break
                            
                            if not has_valid_moves:
                                # Verifica se o jogador atual ainda tem movimentos
                                current_has_moves = False
                                for r in range(game.board_size):
                                    for c in range(game.board_size):
                                        if game.board[r][c] is None and game.is_valid_move(r, c, player["color"]):
                                            current_has_moves = True
                                            break
                                    if current_has_moves:
                                        break
                                
                                if current_has_moves:
                                    next_color = player["color"]  # Mantém o mesmo jogador
                                    # Envia mensagem informando que não há movimentos válidos
                                    no_moves_msg = {
                                        "type": "move",
                                        "row": row,
                                        "col": col,
                                        "color": player["color"],
                                        "next_turn": next_color,
                                        "no_valid_moves": True
                                    }
                                    self.broadcast_to_game(game_id, no_moves_msg)
                                else:
                                    # Fim do jogo - nenhum jogador pode mover
                                    time.sleep(0.1)
                                    self.handle_game_over(game_id)
                                    return
                            
                            game_data["current_turn"] = next_color
                            
                            ## Envia mensagem do sistema informando o próximo jogador
                            #next_player = next(p for p in game_data["players"] if p["color"] == next_color)
                            #system_msg = {
                            #    "type": "chat",
                            #    "color": "system",
                            #    "player_name": "Sistema",
                            #    "message": f"Vez do jogador {next_player['name']} (Peças {'Pretas' if next_color == 'black' else 'Brancas'})"
                            #}
                            #self.broadcast_to_game(game_id, system_msg)
                
                elif msg["type"] == "chat":
                    player = next(p for p in game_data["players"] if p["socket"] == client_socket)
                    chat_msg = {
                        "type": "chat",
                        "color": player["color"],
                        "player_name": msg["player_name"],
                        "message": msg["message"]
                    }
                    self.broadcast_to_game(game_id, chat_msg)
            
            except Exception as e:
                print(f"Erro ao processar mensagem: {e}")
                self.remove_client(client_socket)
                break
    
    def broadcast_to_game(self, game_id, msg):
        game_data = self.games[game_id]
        for player in game_data["players"]:
            try:
                player["socket"].send(json.dumps(msg).encode())
            except Exception as e:
                print(f"Erro ao enviar mensagem para jogador: {e}")
                self.remove_client(player["socket"])
    
    def broadcast_game_start(self, game_id):
        game_data = self.games[game_id]
        msg = {
            "type": "game_start",
            "current_turn": "black"
        }
        self.broadcast_to_game(game_id, msg)
    
    def remove_client(self, client_socket):
        for game_id, game_data in self.games.items():
            for player in game_data["players"]:
                if player["socket"] == client_socket:
                    self.log(f"Jogador '{player['name']}' desconectou-se do servidor")
            game_data["players"] = [p for p in game_data["players"] if p["socket"] != client_socket]
        try:
            client_socket.close()
        except:
            pass
    
    def handle_game_over(self, game_id):
        game_data = self.games[game_id]
        game = game_data["game"]
        
        # Conta as peças usando o estado do jogo no servidor
        black_count = 0
        white_count = 0
        for row in range(game.board_size):
            for col in range(game.board_size):
                if game.board[row][col] == "black":
                    black_count += 1
                elif game.board[row][col] == "white":
                    white_count += 1
        
        # Determina o vencedor
        if black_count > white_count:
            winner = "black"
        elif white_count > black_count:
            winner = "white"
        else:
            winner = "tie"
        
        # Envia mensagem de fim de jogo
        game_over_msg = {
            "type": "game_over",
            "winner": winner,
            "black_count": black_count,
            "white_count": white_count
        }
        self.broadcast_to_game(game_id, game_over_msg)
        
        # Remove o jogo da lista de jogos ativos
        del self.games[game_id]

    def stop(self):
        self.running = False
        self.server.close()
        for game_id, game_data in self.games.items():
            for player in game_data["players"]:
                try:
                    player["socket"].close()
                except:
                    pass
        self.log("Servidor encerrado")

if __name__ == "__main__":
    server = OthelloServer()
    server.start()
