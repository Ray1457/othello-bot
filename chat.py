import edax


if __name__ == '__main__':
    Edax = edax.start_edax()


def create_board():
    board = [[0 for _ in range(8)] for _ in range(8)]
    board[3][3] = board[4][4] = -1  # White pieces
    board[3][4] = board[4][3] = 1   # Black pieces
    return board

def print_board(board):
    print("  0 1 2 3 4 5 6 7")
    for i, row in enumerate(board):
        print(f"{i}", end=" ")
        for cell in row:
            if cell == 1:
                print("B", end=" ")
            elif cell == -1:
                print("W", end=" ")
            else:
                print(".", end=" ")
        print()

def get_valid_moves(board_state, player_color):
    valid_moves = []
    for row in range(8):
        for col in range(8):
            if is_valid_move(board_state, row, col, player_color):
                valid_moves.append((row, col))
    return valid_moves

def is_valid_move(board_state, row, col, player_color):
    if board_state[row][col] != 0:
        return False
        
    directions = [(0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1), (-1,0), (-1,1)]
    
    for dx, dy in directions:
        if check_direction(board_state, row, col, dx, dy, player_color):
            return True
    return False

def check_direction(board_state, row, col, dx, dy, player_color):
    x, y = row + dx, col + dy
    has_opponent_pieces = False
    
    while 0 <= x < 8 and 0 <= y < 8:
        if board_state[x][y] == 0:
            return False
        if board_state[x][y] == player_color:
            return has_opponent_pieces
        has_opponent_pieces = True
        x, y = x + dx, y + dy
    return False

def make_move(board_state, row, col, player_color):
    directions = [(0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1), (-1,0), (-1,1)]
    board_state[row][col] = player_color
    
    for dx, dy in directions:
        if check_direction(board_state, row, col, dx, dy, player_color):
            x, y = row + dx, col + dy
            while board_state[x][y] == -player_color:
                board_state[x][y] = player_color
                x, y = x + dx, y + dy

def evaluate_position(board_state, player_color):
    my_pieces = sum([row.count(player_color) for row in board_state])
    opponent_pieces = sum([row.count(-player_color) for row in board_state])
    piece_advantage = my_pieces - opponent_pieces
    
    corner_positions = [(0,0), (0,7), (7,0), (7,7)]
    corner_score = sum([3 if board_state[x][y] == player_color else -3 
                       for x, y in corner_positions if board_state[x][y] != 0])
    
    return piece_advantage + corner_score

def look_ahead(board_state, search_depth, alpha, beta, is_maximizing, player_color):
    if search_depth == 0:
        return evaluate_position(board_state, player_color)
        
    possible_moves = get_valid_moves(board_state, 
                                   player_color if is_maximizing else -player_color)
    
    if not possible_moves:
        return evaluate_position(board_state, player_color)
    
    if is_maximizing:
        best_score = float('-inf')
        for row, col in possible_moves:
            future_board = [row[:] for row in board_state]
            make_move(future_board, row, col, player_color)
            
            score = look_ahead(future_board, search_depth-1, alpha, beta, Fal se, player_color)
            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score
    else:
        worst_score = float('inf')
        for row, col in possible_moves:
            future_board = [row[:] for row in board_state]
            make_move(future_board, row, col, -player_color)
            
            score = look_ahead(future_board, search_depth-1, alpha, beta, True, player_color)
            worst_score = min(worst_score, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return worst_score

def move(board_state, player_color):
    possible_moves = get_valid_moves(board_state, player_color)
    
    if not possible_moves:
        return None
    
    best_move = None
    best_score = float('-inf')
    
    empty_spaces = sum(row.count(0) for row in board_state)
    search_depth = 40 if empty_spaces <= 10 else 7
    
    for row, col in possible_moves:
        future_board = [row[:] for row in board_state]
        make_move(future_board, row, col, player_color)
        
        score = look_ahead(future_board, search_depth-1, float('-inf'), float('inf'), 
                          False, player_color)
        if score > best_score:
            best_score = score
            best_move = (row, col)
            
    return best_move
class player_m:
    @staticmethod
    def move(player_color, current_board):
        valid_moves = get_valid_moves(current_board, player_color)
        valid_moves_set = set(valid_moves)  # Use a set for quick lookup
        
        # Display the board with valid moves marked as 'V'
        print("  0 1 2 3 4 5 6 7")
        for i in range(8):
            print(f"{i} ", end="")
            for j in range(8):
                if (i, j) in valid_moves_set:
                    print("V", end=" ")
                elif current_board[i][j] == 1:
                    print("B", end=" ")
                elif current_board[i][j] == -1:
                    print("W", end=" ")
                else:
                    print(".", end=" ")
            print()
        
        if not valid_moves:
            print("No valid moves available.")
            return None
        
        print("\nValid moves:", valid_moves)
        
        # Input validation loop
        while True:
            try:
                x,y = edax.get_move(current_board, player_color, Edax)
                print(x,y)
                if (x,y) in valid_moves:
                    return (x,y)
                else:
                    print(f"Invalid move. Choose one of {valid_moves}.")
            except ValueError:
                print("Invalid input. Enter numeric coordinates between 0 and 7.")




def play_game(bot1, bot2, verbose=True):
    board = create_board()
    current_player = 1
    consecutive_passes = 0
    
    while consecutive_passes < 2:
        if verbose:
            print_board(board)
            print(f"{'Black' if current_player == 1 else 'White'} to move")
        
        current_bot = bot1 if current_player == 1 else bot2
        move_result = current_bot(board, current_player)
        
        if move_result is None:  # No valid moves for the current player
            consecutive_passes += 1
            print(f"{'Black' if current_player == 1 else 'White'} passes.")
        else:
            row, col = move_result
            make_move(board, row, col, current_player)
            consecutive_passes = 0  # Reset passes when a valid move is made
            if verbose:
                print(f"{'Black' if current_player == 1 else 'White'} moves to {row},{col}")
        
        current_player = -current_player  # Switch player
        print()
    
    # Final scoring
    black_count = sum(row.count(1) for row in board)
    white_count = sum(row.count(-1) for row in board)
    
    if verbose:
        print("Game Over!")
        print(f"Final Score - Black: {black_count}, White: {white_count}")
        print_board(board)
    
    return black_count, white_count

        

if __name__ == "__main__":
    # Example: Play a game between a bot and a player
    black_score, white_score = play_game(
        move, 
        lambda board, player_color: player_m.move(player_color, board),
        verbose=True
    )
