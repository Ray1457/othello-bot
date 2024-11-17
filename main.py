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

    return valid_moves


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
    directions = [(0, 1), (1, 1), (1, 0), (1, -1),
                  (0, -1), (-1, -1), (-1, 0), (-1, 1)]
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

    corner_positions = [(0, 0), (0, 7), (7, 0), (7, 7)]
    corner_score = sum([3 if board_state[x][y] == player_color else -3
                        for x, y in corner_positions if board_state[x][y] != 0])
    move_advantage = (
        len(get_valid_moves(board_state, player_color))+ 
        len(get_valid_moves(board_state , -player_color))
        )
    position_advantage = piece_advantage + corner_score
    advantage = move_advantage + position_advantage

    return advantage


def look_ahead(board_state, search_depth, alpha, beta, is_maximizing, player_color):
    if search_depth == 0:
        return evaluate_position(board_state, player_color)

    possible_moves = get_valid_moves(
        board_state, player_color if is_maximizing else -player_color)

    if not possible_moves:
        return evaluate_position(board_state, player_color)

    if is_maximizing:
        best_score = float('-inf')
        for row, col in possible_moves:
            future_board = [row[:] for row in board_state]
            make_move(future_board, row, col, player_color)

            score = look_ahead(future_board, search_depth-1,
                               alpha, beta, False, player_color)
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

            score = look_ahead(future_board, search_depth-1,
                               alpha, beta, True, player_color)
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
    search_depth = 40 if empty_spaces <= 10 else 6

    for row, col in possible_moves:
        future_board = [row[:] for row in board_state]
        make_move(future_board, row, col, player_color)

        score = look_ahead(future_board, search_depth-1, float('-inf'),
                           float('inf'), False, player_color)
        if score > best_score:
            best_score = score
            best_move = (row, col)

    return best_move


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
    black_score, white_score = play_game(
        player,
        move,
        verbose=True
    )
