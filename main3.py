from concurrent.futures import ProcessPoolExecutor
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


def look_ahead(board_state, search_depth, alpha, beta, is_maximizing, player_color):
    if search_depth == 0:
        return evaluate_position(board_state, player_color)

    possible_moves,move_dirs = get_valid_moves(
        board_state, player_color if is_maximizing else -player_color)

    if not possible_moves:
        return evaluate_position(board_state, player_color)

    if is_maximizing:
        best_score = float('-inf')
        for i in range(len(possible_moves)):
            row,col = possible_moves[i]
            dire = move_dirs[i]
            future_board = [row[:] for row in board_state]
            make_move(future_board, row, col, dire, player_color)

            score = look_ahead(future_board, search_depth-1,
                               alpha, beta, False, player_color)
            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score
    else:
        worst_score = float('inf')
        for i in range(len(possible_moves)):
            row,col = possible_moves[i]
            dire = move_dirs[i]
            future_board = [row[:] for row in board_state]
            make_move(future_board, row, col, dire, -player_color)

            score = look_ahead(future_board, search_depth-1,
                               alpha, beta, True, player_color)
            worst_score = min(worst_score, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return worst_score

def evaluate_move(index, possible_moves, move_dirs, board_state, search_depth, player_color):
    row, col = possible_moves[index]
    dire = move_dirs[index]
    future_board = [row[:] for row in board_state]
    make_move(future_board, row, col, dire, player_color)

    return (
        row,
        col,
        parallel_look_ahead(
            future_board,
            search_depth - 1,
            float('-inf'),
            float('inf'),
            False,
            player_color
        )
    )


def parallel_look_ahead(board_state, search_depth, alpha, beta, is_maximizing, player_color):
    if search_depth == 0:
        return evaluate_position(board_state, player_color)

    possible_moves, move_dirs = get_valid_moves(
        board_state, player_color if is_maximizing else -player_color
    )

    if not possible_moves:
        return evaluate_position(board_state, player_color)

    def evaluate_future_move(index):
        row, col = possible_moves[index]
        dire = move_dirs[index]
        future_board = [row[:] for row in board_state]
        make_move(future_board, row, col, dire,
                  player_color if is_maximizing else -player_color)

        return look_ahead(
            future_board, 
            search_depth - 1, 
            alpha, beta, 
            not is_maximizing, 
            player_color
        )

    if is_maximizing:
        best_score = float('-inf')
        with ProcessPoolExecutor() as executor:
            scores = list(executor.map(evaluate_future_move, range(len(possible_moves))))

        for score in scores:
            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score
    else:
        worst_score = float('inf')
        with ProcessPoolExecutor() as executor:
            scores = list(executor.map(evaluate_future_move, range(len(possible_moves))))

        for score in scores:
            worst_score = min(worst_score, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return worst_score


def move(board_state, player_color):
    possible_moves, move_dirs = get_valid_moves(board_state, player_color)

    if not possible_moves:
        return None

    best_move = None
    best_score = float('-inf')

    empty_spaces = sum(row.count(0) for row in board_state)
    search_depth = 40 if empty_spaces <= 10 else 6

    with ProcessPoolExecutor() as executor:
        results = list(
            executor.map(
                evaluate_move,
                range(len(possible_moves)),
                [possible_moves] * len(possible_moves),
                [move_dirs] * len(possible_moves),
                [board_state] * len(possible_moves),
                [search_depth] * len(possible_moves),
                [player_color] * len(possible_moves),
            )
        )

    for row, col, score in results:
        if score > best_score:
            best_score = score
            best_move = (row, col)

    return best_move



def get_valid_moves(board_state, player_color):
    player_pcs = [
        [i, j] for i in range(len(board_state))
        for j in range(len(board_state[i]))
        if board_state[i][j] == player_color
    ]

    dirs = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    valid_moves = []
    dir_moves = []

    for pc in player_pcs:
        for d in dirs:
            new = [pc[0] + d[0], pc[1] + d[1]]
            c = 0
            # Traverse in the current direction
            while (
                0 <= new[0] < len(board_state) and
                0 <= new[1] < len(board_state[0]) and
                board_state[new[0]][new[1]] == -player_color
            ):
                new = [new[0] + d[0], new[1] + d[1]]
                c += 1

            # Check if the final square is a valid move
            if (
                c > 0 and
                0 <= new[0] < 8 and
                0 <= new[1] < 8 and
                board_state[new[0]][new[1]] == 0
            ):
                valid_moves.append(tuple(new))
                dir_moves.append(d)

    return valid_moves, dir_moves


def make_move(board_state, row, col, direction, player_color):
    board_state[row][col] = player_color

    dx, dy = direction
    x, y = row + dx, col + dy
    flip_positions = []
    while 0 <= x < 8 and 0 <= y < 8 and board_state[x][y] == -player_color:
        flip_positions.append((x, y))
        x, y = x + dx, y + dy
    
    if 0 <= x < 8 and 0 <= y < 8 and board_state[x][y] == player_color:
        for fx, fy in flip_positions:
            board_state[fx][fy] = player_color


def evaluate_position(board_state, player_color):
    my_pieces = sum([row.count(player_color) for row in board_state])
    opponent_pieces = sum([row.count(-player_color) for row in board_state])
    piece_advantage = my_pieces - opponent_pieces

    corner_positions = [(0, 0), (0, 7), (7, 0), (7, 7)]
    corner_score = sum([3 if board_state[x][y] == player_color else -3
                        for x, y in corner_positions if board_state[x][y] != 0])

    return piece_advantage + corner_score



def player(board_state, player_color):
    valid_moves = get_valid_moves(board_state, player_color)
    valid_moves_set = set(valid_moves)

    print_board(board_state)
    print("\nValid moves:", valid_moves)
    if not valid_moves : return None
    while True:
        try:
            x, y = edax.get_move(board_state, player_color, Edax)
            if (x, y) in valid_moves_set:
                return x, y
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

        if move_result is None:
            consecutive_passes += 1
            print(f"{'Black' if current_player == 1 else 'White'} passes.")
        else:
            row, col = move_result
            make_move(board, row, col, current_player)
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
    # if multiprocessing.get_start_method(allow_none=True) != "fork":
    #     multiprocessing.set_start_method("fork")
    play_game(move, player, verbose=True)
