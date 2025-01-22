import Pyro4
import threading
from game_logic import OthelloGame
import time
import socket

@Pyro4.expose
class OthelloServer:
    def __init__(self, host='0.0.0.0', port=5000, log_callback=None):
        self.host = host
        self.port = port
        self.log_callback = log_callback
        self.running = True
        self.games = {}
        self.chat_messages = {}  # {game_id: {message_id: {message_data, read_by: set()}}}
        self.message_counter = 0  # Contador global de mensagens
        
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

    def connect_player(self, player_name, game_id="game1"):
        try:
            if game_id not in self.games:
                self.games[game_id] = {
                    "game": OthelloGame(),
                    "players": [],
                    "current_turn": "black",
                    "game_just_started": False
                }
            
            game_data = self.games[game_id]
            
            if len(game_data["players"]) < 2:
                color = "black" if not game_data["players"] else "white"
                
                game_data["players"].append({
                    "color": color,
                    "name": player_name
                })
                
                self.log(f"Jogador '{player_name}' conectou-se ao servidor")
                
                game_started = len(game_data["players"]) == 2
                
                if game_started:
                    game_data["game_just_started"] = True
                    return {
                        "status": "connected",
                        "color": color,
                        "game_started": True
                    }
                
                return {
                    "status": "connected",
                    "color": color,
                    "game_started": False
                }
            
            return {"status": "error", "message": "Jogo cheio"}
            
        except Exception as e:
            self.log(f"Erro ao conectar jogador: {e}", "ERROR")
            return {"status": "error", "message": str(e)}

    def make_move(self, game_id, player_name, row, col):
        try:
            game_data = self.games[game_id]
            
            # Verifica se o jogo já terminou
            if game_data.get("game_over", False):
                return {"status": "error", "message": "O jogo já terminou"}
            
            game = game_data["game"]
            player = next(p for p in game_data["players"] if p["name"] == player_name)
            
            if player["color"] != game_data["current_turn"]:
                return {"status": "error", "message": "Não é sua vez"}
            
            if not game.is_valid_move(row, col, player["color"]):
                return {"status": "error", "message": "Movimento inválido"}
            
            game.make_move(row, col, player["color"])
            next_color = "white" if player["color"] == "black" else "black"
            
            # Verifica movimentos válidos para o próximo jogador
            has_valid_moves = self._check_valid_moves(game, next_color)
            
            if not has_valid_moves:
                current_has_moves = self._check_valid_moves(game, player["color"])
                
                if current_has_moves:
                    next_color = player["color"]
                    game_data["current_turn"] = next_color
                    return {
                        "status": "success",
                        "row": row,
                        "col": col,
                        "color": player["color"],
                        "next_turn": next_color,
                        "no_valid_moves": True
                    }
                else:
                    return self.handle_game_over(game_id)
            
            game_data["current_turn"] = next_color
            return {
                "status": "success",
                "row": row,
                "col": col,
                "color": player["color"],
                "next_turn": next_color
            }
            
        except Exception as e:
            self.log(f"Erro ao fazer movimento: {e}", "ERROR")
            return {"status": "error", "message": str(e)}

    def send_chat_message(self, game_id, player_name, message):
        try:
            if game_id not in self.chat_messages:
                self.chat_messages[game_id] = {}
            
            game_data = self.games[game_id]
            player = next(p for p in game_data["players"] if p["name"] == player_name)
            
            self.message_counter += 1
            message_id = self.message_counter
            
            chat_message = {
                "id": message_id,
                "color": player["color"],
                "player_name": player_name,
                "message": message,
                "timestamp": time.time(),
                "read_by": set()
            }
            
            self.chat_messages[game_id][message_id] = chat_message
            return {
                "status": "success",
                "type": "chat",
                **{k: v for k, v in chat_message.items() if k != 'read_by'}
            }
            
        except Exception as e:
            self.log(f"Erro ao enviar mensagem: {e}", "ERROR")
            return {"status": "error", "message": str(e)}

    def _check_valid_moves(self, game, color):
        for r in range(game.board_size):
            for c in range(game.board_size):
                if game.board[r][c] is None and game.is_valid_move(r, c, color):
                    return True
        return False

    def handle_game_over(self, game_id):
        try:
            game_data = self.games[game_id]
            game = game_data["game"]
            black_count, white_count = game.get_score()
            
            if black_count > white_count:
                winner = "black"
            elif white_count > black_count:
                winner = "white"
            else:
                winner = "tie"
            
            # Marca o jogo como terminado
            game_data["game_over"] = True
            game_data["current_turn"] = None
            
            return {
                "status": "success",
                "type": "game_over",
                "winner": winner,
                "black_count": black_count,
                "white_count": white_count,
                "board": game.board
            }
        except Exception as e:
            self.log(f"Erro ao finalizar o jogo: {e}", "ERROR")
            return {"status": "error", "message": str(e)}

    def get_game_state(self, game_id, player_name):
        try:
            game_data = self.games.get(game_id)
            if not game_data:
                return {"status": "error", "message": "Jogo não encontrado"}
            
            # Verifica se há solicitação de desistência pendente
            surrender_request = game_data.get("surrender_request")
            if (surrender_request and 
                surrender_request.get("pending") and 
                surrender_request["requester"] != player_name):
                
                return {
                    "status": "success",
                    "type": "surrender_request",
                    "requester": surrender_request["requester"]
                }
            
            # Se o jogo já terminou por desistência
            if game_data.get("game_over", False) and game_data.get("surrender_info"):
                return {
                    "status": "success",
                    "type": "game_over_surrender",
                    "winner": game_data["surrender_info"]["winner"],
                    "surrender": True,
                    "surrendered_by": game_data["surrender_info"]["surrendered_by"]
                }
            
            # Se o jogo já terminou normalmente
            if game_data.get("game_over", False):
                return self.handle_game_over(game_id)
            
            # Filtra mensagens não lidas pelo jogador atual
            unread_messages = []
            if game_id in self.chat_messages:
                for msg_id, msg in self.chat_messages[game_id].items():
                    if player_name not in msg["read_by"]:
                        msg["read_by"].add(player_name)
                        unread_messages.append({
                            k: v for k, v in msg.items() if k != 'read_by'
                        })
            
            game = game_data["game"]
            current_turn = game_data["current_turn"]
            
            # Verifica se o jogo acabou de começar
            if game_data.get("game_just_started", False):
                game_data["game_just_started"] = False  # Reset a flag
                return {
                    "status": "success",
                    "type": "game_started",
                    "current_turn": current_turn,
                    "players": game_data["players"]
                }
            
            # Verifica se há movimentos válidos
            has_valid_moves = self._check_valid_moves(game, current_turn)
            if not has_valid_moves:
                opponent_color = "white" if current_turn == "black" else "black"
                opponent_has_moves = self._check_valid_moves(game, opponent_color)
                
                if not opponent_has_moves:
                    return self.handle_game_over(game_id)
                
                return {
                    "status": "success",
                    "type": "no_valid_moves",
                    "current_turn": opponent_color,
                    "no_valid_moves": True
                }
            
            # Retorna o estado atual do jogo
            black_count, white_count = game.get_score()
            return {
                "status": "success",
                "type": "game_state",
                "current_turn": current_turn,
                "black_count": black_count,
                "white_count": white_count,
                "board": game.board,
                "players": game_data["players"],
                "chat_messages": unread_messages  # Adiciona mensagens ao estado
            }
            
        except Exception as e:
            self.log(f"Erro ao obter estado do jogo: {e}", "ERROR")
            return {"status": "error", "message": str(e)}

    def reset_game(self, game_id):
        try:
            if game_id in self.games:
                # Preserva os jogadores mas reinicia o jogo
                players = self.games[game_id]["players"]
                
                # Reseta o estado do jogo
                self.games[game_id] = {
                    "game": OthelloGame(),
                    "players": players,
                    "current_turn": "black",
                    "game_just_started": True,
                    "game_over": False  # Novo flag para controlar estado do jogo
                }
                
                # Limpa as mensagens do chat
                if game_id in self.chat_messages:
                    self.chat_messages[game_id] = {}
                
                # Notifica todos os jogadores sobre o reinício
                for player in players:
                    player["ready_for_new_game"] = True
                
                return {
                    "status": "success",
                    "type": "game_reset",
                    "current_turn": "black"
                }
        except Exception as e:
            self.log(f"Erro ao reiniciar o jogo: {e}", "ERROR")
            return {"status": "error", "message": str(e)}

    def request_surrender(self, game_id, player_name):
        try:
            game_data = self.games[game_id]
            if game_data.get("game_over", False):
                return {"status": "error", "message": "O jogo já terminou"}
            
            opponent = next(p for p in game_data["players"] if p["name"] != player_name)
            
            # Armazena a solicitação de desistência
            game_data["surrender_request"] = {
                "requester": player_name,
                "pending": True
            }
            
            return {
                "status": "success",
                "type": "surrender_request",
                "player_name": player_name
            }
        except Exception as e:
            self.log(f"Erro ao solicitar desistência: {e}", "ERROR")
            return {"status": "error", "message": str(e)}

    def respond_to_surrender(self, game_id, player_name, accepted):
        try:
            game_data = self.games[game_id]
            if not game_data.get("surrender_request"):
                return {"status": "error", "message": "Não há solicitação de desistência pendente"}
            
            surrendered_by = game_data["surrender_request"]["requester"]
            
            if accepted:
                # Finaliza o jogo com vitória do oponente
                game_data["game_over"] = True
                game_data["current_turn"] = None
                # Armazena informações da desistência
                game_data["surrender_info"] = {
                    "winner": player_name,
                    "surrendered_by": surrendered_by
                }
                
                return {
                    "status": "success",
                    "type": "game_over_surrender",
                    "winner": player_name,
                    "surrender": True,
                    "surrendered_by": surrendered_by
                }
            else:
                print("Desistência recusada")
                print(game_data)
                # Cancela a solicitação de desistência
                game_data.pop("surrender_request")
                return {
                    "status": "success",
                    "type": "surrender_cancelled",
                    "requester": surrendered_by
                }
        except Exception as e:
            self.log(f"Erro ao processar resposta de desistência: {e}", "ERROR")
            return {"status": "error", "message": str(e)}

def start_server(host='0.0.0.0', port=5000):
    server = OthelloServer(host=host, port=port)
    daemon = Pyro4.Daemon(host=host, port=port)
    uri = daemon.register(server, "othello.server")
    print(f"URI do servidor: {uri}")
    daemon.requestLoop()

if __name__ == "__main__":
    start_server()
