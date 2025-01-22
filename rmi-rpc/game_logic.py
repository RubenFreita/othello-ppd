class OthelloGame:
    def __init__(self):
        self.board_size = 8
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.turn = "black"
        self.init_board()
        
    def init_board(self):
        mid = self.board_size // 2
        self.board[mid-1][mid-1] = "white"
        self.board[mid][mid] = "white"
        self.board[mid-1][mid] = "black"
        self.board[mid][mid-1] = "black"
    
    def is_valid_move(self, row, col, color):
        if self.board[row][col] is not None:
            return False
        
        opponent_color = "white" if color == "black" else "black"
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        for dr, dc in directions:
            r, c = row + dr, col + dc
            found_opponent = False
            
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board[r][c] is None:
                    break
                
                if self.board[r][c] == opponent_color:
                    found_opponent = True
                elif self.board[r][c] == color and found_opponent:
                    return True
                else:
                    break
                
                r += dr
                c += dc
        
        return False
    
    def check_directions(self, row, col, color):
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        opponent_color = "white" if color == "black" else "black"
        valid = False
        
        for dr, dc in directions:
            r, c = row + dr, col + dc
            found_opponent = False
            temp_valid = False
            
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board[r][c] is None:
                    break
                
                current_color = self.board[r][c]
                
                if current_color == opponent_color:
                    found_opponent = True
                elif current_color == color and found_opponent:
                    temp_valid = True
                    break
                else:
                    break
                
                r += dr
                c += dc
            
            if temp_valid:
                valid = True
                
        return valid
    
    def make_move(self, row, col, color):
        if not self.is_valid_move(row, col, color):
            return False
        
        self.board[row][col] = color
        self.flip_pieces(row, col, color)
        return True
    
    def flip_pieces(self, row, col, color):
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        opponent_color = "white" if color == "black" else "black"
        flipped_pieces = []
        
        for dr, dc in directions:
            pieces_to_flip = []
            r, c = row + dr, col + dc
            
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board[r][c] is None:
                    break
                
                current_color = self.board[r][c]
                
                if current_color == opponent_color:
                    pieces_to_flip.append((r, c))
                elif current_color == color and pieces_to_flip:
                    flipped_pieces.extend(pieces_to_flip)
                    for pr, pc in pieces_to_flip:
                        self.board[pr][pc] = color
                    break
                else:
                    break
                
                r += dr
                c += dc
                
        return flipped_pieces
    
    def get_valid_moves(self, color):
        valid_moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.is_valid_move(row, col, color):
                    valid_moves.append((row, col))
        return valid_moves
    
    def get_score(self):
        black_count = sum(row.count("black") for row in self.board)
        white_count = sum(row.count("white") for row in self.board)
        return black_count, white_count
