import subprocess
import time

def start_edax(edax_path="./edax"):
    """Starts the Edax engine and returns the subprocess object."""
    return subprocess.Popen(
        [edax_path, '--level', '5'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

def read_input(edax):
    response = []
    while True:
        line = edax.stdout.readline()
        response.append(line)
        if ">" in line:
            break
    return "\n".join(response)


def send_command(edax, command):
    print('sending' , command, 'to edax')
    edax.stdin.write(f"{command}\n")
    edax.stdin.flush()
    return read_input(edax)


def arr_to_fen(board: list[list[int]]) -> str:
    piece_map = {0: '.', 1: 'X', -1: 'O'}
    fen = []
    
    for row in board:
        fen_row = ''.join(piece_map[cell] for cell in row)
        fen.append(fen_row)
    
    return '/'.join(fen)

def fen_to_arr(fen: str) -> list[list[int]]:
    piece_map = {'.': 0, 'X': 1, 'O': -1}
    board = []

    for fen_row in fen.split('/'):
        board_row = [piece_map[char] for char in fen_row]
        board.append(board_row)
    
    return board

    

def edax_to_bot(move: str) -> tuple[int, int]:
    return (int(move[1]) - 1, ord(move[0].lower()) - ord('a') )

def bot_to_edax(move : tuple[int, int]) -> str:
    x,y = move
    return f"{chr(x + ord('a'))}{y + 1}"



def get_best_move(fen, turn, edax):
    send_command(edax, f'setboard {fen} {turn}')
    send_command(edax, 'go')
    move = ''
    while True:
        line = edax.stdout.readline()
        if 'Edax plays ' in line:
            move = line.split()[-1]
            break
    return move

def get_move(board_state, turn, edax):
    player_map = {
        1:'X',
        -1:'O'
    }
    fen = arr_to_fen(board_state)
    player = player_map[turn]

    move  = get_best_move(fen, player, edax)

    bot_move = edax_to_bot(move)

    return bot_move


