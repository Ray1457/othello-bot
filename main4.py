import multiprocessing as mp
from functools import lru_cache
import edax
from typing import List, Tuple, Set, Optional
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor

# Using dataclass for better memory efficiency and faster attribute access
@dataclass(frozen=True)
class BoardState:
    board: tuple  # Immutable representation of the board
    
    @classmethod
    def from_list(cls, board: List[List[int]]):
        return cls(tuple(tuple(row) for row in board))
    
    def to_list(self) -> List[List[int]]:
        return [list(row) for row in self.board]

class GameCache:
    _valid_moves_cache = {}
    # Position weights matrix as a tuple of tuples for immutability
    _position_weights = (
        (120, -20,  20,   5,   5,  20, -20, 120),
        (-20, -40,  -5,  -5,  -5,  -5, -40, -20),
        ( 20,  -5,  15,   3,   3,  15,  -5,  20),
        (  5,  -5,   3,   3,   3,   3,  -5,   5),
        (  5,  -5,   3,   3,   3,   3,  -5,   5),
        ( 20,  -5,  15,   3,   3,  15,  -5,  20),
        (-20, -40,  -5,  -5,  -5,  -5, -40, -20),
        (120, -20,  20,   5,   5,  20, -20, 120)
    )
    
    @classmethod
    def clear(cls):
        cls._valid_moves_cache.clear()

def create_board() -> List[List[int]]:
    board = [[0 for _ in range(8)] for _ in range(8)]
    board[3][3] = board[4][4] = -1
    board[3][4] = board[4][3] = 1
    return board

def print_board(board: List[List[int]]) -> None:
    print("  0 1 2 3 4 5 6 7")
    for i, row in enumerate(board):
        print(f"{i}", end=" ")
        for cell in row:
            print("B " if cell == 1 else "W " if cell == -1 else ". ", end="")
        print()

@lru_cache(maxsize=10000)
def get_valid_moves(board_state: BoardState, player_color: int) -> Set[Tuple[int, int]]:
    cache_key = (board_state, player_color)
    if cache_key in GameCache._valid_moves_cache:
        return GameCache._valid_moves_cache[cache_key]

    board = board_state.board
    valid_moves = set()
    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for i in range(8):
        for j in range(8):
            if board[i][j] == player_color:
                for dx, dy in dirs:
                    x, y = i + dx, j + dy
                    capture_count = 0
                    
                    while 0 <= x < 8 and 0 <= y < 8 and board[x][y] == -player_color:
                        x, y = x + dx, y + dy
                        capture_count += 1
                        
                    if (capture_count > 0 and 0 <= x < 8 and 0 <= y < 8 and 
                        board[x][y] == 0):
                        valid_moves.add((x, y))
    
    GameCache._valid_moves_cache[cache_key] = valid_moves
    return valid_moves

def make_move(board: List[List[int]], row: int, col: int, 
              player_color: int) -> List[List[int]]:
    new_board = [row[:] for row in board]
    new_board[row][col] = player_color
    
    dirs = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
    for dx, dy in dirs:
        x, y = row + dx, col + dy
        to_flip = []
        
        while 0 <= x < 8 and 0 <= y < 8 and new_board[x][y] == -player_color:
            to_flip.append((x, y))
            x, y = x + dx, y + dy
            
        if to_flip and 0 <= x < 8 and 0 <= y < 8 and new_board[x][y] == player_color:
            for flip_x, flip_y in to_flip:
                new_board[flip_x][flip_y] = player_color
                
    return new_board

@lru_cache(maxsize=10000)
def evaluate_position(board_state: BoardState, player_color: int) -> int:
    board = board_state.board
    opponent_color = -player_color
    
    # Piece count weighted by position
    player_score = 0
    opponent_score = 0
    for i in range(8):
        for j in range(8):
            if board[i][j] == player_color:
                player_score += GameCache._position_weights[i][j]
            elif board[i][j] == opponent_color:
                opponent_score += GameCache._position_weights[i][j]
    
    # Mobility (count of valid moves)
    player_moves = len(get_valid_moves(board_state, player_color))
    opponent_moves = len(get_valid_moves(board_state, opponent_color))
    mobility = (player_moves - opponent_moves) * 10
    
    return player_score - opponent_score + mobility

def look_ahead_worker(args) -> int:
    board_state, depth, alpha, beta, is_maximizing, player_color = args
    return _look_ahead(board_state, depth, alpha, beta, is_maximizing, player_color)

@lru_cache(maxsize=10000)
def _look_ahead(board_state: BoardState, depth: int, alpha: float, beta: float,
                is_maximizing: bool, player_color: int) -> int:
    if depth == 0:
        return evaluate_position(board_state, player_color)

    current_color = player_color if is_maximizing else -player_color
    possible_moves = get_valid_moves(board_state, current_color)

    if not possible_moves:
        return evaluate_position(board_state, player_color)

    if is_maximizing:
        best_score = float('-inf')
        for row, col in possible_moves:
            new_board = make_move(board_state.to_list(), row, col, current_color)
            new_board_state = BoardState.from_list(new_board)
            
            score = _look_ahead(new_board_state, depth-1, alpha, beta, False, 
                              player_color)
            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score
    else:
        worst_score = float('inf')
        for row, col in possible_moves:
            new_board = make_move(board_state.to_list(), row, col, current_color)
            new_board_state = BoardState.from_list(new_board)
            
            score = _look_ahead(new_board_state, depth-1, alpha, beta, True, 
                              player_color)
            worst_score = min(worst_score, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return worst_score

def move(board_state: List[List[int]], player_color: int) -> Optional[Tuple[int, int]]:
    board_state_immutable = BoardState.from_list(board_state)
    possible_moves = get_valid_moves(board_state_immutable, player_color)

    if not possible_moves:
        return None

    empty_spaces = sum(row.count(0) for row in board_state)
    search_depth = 40 if empty_spaces <= 10 else 6

    # Prepare arguments for parallel processing
    move_args = []
    for row, col in possible_moves:
        future_board = make_move(board_state, row, col, player_color)
        future_board_state = BoardState.from_list(future_board)
        move_args.append((
            future_board_state, search_depth-1, float('-inf'), float('inf'), 
            False, player_color
        ))

    # Use ProcessPoolExecutor for parallel processing
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        scores = list(executor.map(look_ahead_worker, move_args))

    # Find the best move
    best_score = float('-inf')
    best_move = None
    for (row, col), score in zip(possible_moves, scores):
        if score > best_score:
            best_score = score
            best_move = (row, col)

    return best_move

def player(board_state: List[List[int]], player_color: int) -> Optional[Tuple[int, int]]:
    board_state_immutable = BoardState.from_list(board_state)
    valid_moves = get_valid_moves(board_state_immutable, player_color)
    
    print_board(board_state)
    print("\nValid moves:", valid_moves)
    if not valid_moves:
        return None
    
    while True:
        try:
            x, y = edax.get_move(board_state, player_color, Edax)
            if (x, y) in valid_moves:
                return x, y
            print(f"Invalid move. Choose one of {valid_moves}.")
        except ValueError:
            print("Invalid input. Enter numeric coordinates between 0 and 7.")

def play_game(bot1, bot2, verbose: bool = True) -> Tuple[int, int]:
    board = create_board()
    current_player = 1
    consecutive_passes = 0
    GameCache.clear()  # Clear cache at start of new game

    while consecutive_passes < 2:
        if verbose:
            print_board(board)
            print(f"{'Black' if current_player == 1 else 'White'} to move")

        current_bot = bot1 if current_player == 1 else bot2
        move_result = current_bot(board, current_player)

        if move_result is None:
            consecutive_passes += 1
            print(f"{'Black' if current_player == 1 else 'White'} passes.")
        else:
            row, col = move_result
            board = make_move(board, row, col, current_player)
            consecutive_passes = 0
            if verbose:
                print(f"{'Black' if current_player == 1 else 'White'} moves to {row},{col}")

        current_player = -current_player
        print()

    black_count = sum(row.count(1) for row in board)
    white_count = sum(row.count(-1) for row in board)

    if verbose:
        print("Game Over!")
        print(f"Final Score - Black: {black_count}, White: {white_count}")
        print_board(board)

    return black_count, white_count

if __name__ == "__main__":
    Edax = edax.start_edax()
    try:
        black_score, white_score = play_game(player, move, verbose=True)
    finally:
        edax.close_edax(Edax)