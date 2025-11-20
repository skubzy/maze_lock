# server.py

import socket
import threading
import random, time,statistics

HOST = "0.0.0.0"
PORT = 5001


# you can copy your generate_maze from main.py into here too

class GameState:
    def __init__(self, rows, cols, maze):
        self.rows = rows
        self.cols = cols
        self.maze = maze          # 2D list
        self.players = {}         # player_id -> [x, y]
        self.conns = {}           # player_id -> socket
        self.next_id = 1
        self.lock = threading.Lock()


    def add_player(self):
        # create a new player at starting position 1,1
        with self.lock:
            pid = f"p{self.next_id}"
            self.next_id += 1
            self.players[pid] = [1, 1]
            return pid, 1, 1

    def move_player(self, pid, dx, dy):
        # move the player if the target cell is inside maze and not a wall
        with self.lock:
            x, y = self.players[pid]
            nx = x + dx
            ny = y + dy

            # check bounds of maze
            if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                return x, y

            cell = self.maze[ny][nx]

            # wall is value 1 so do not move
            if cell == 1:
                return x, y

            # movement is allowed
            self.players[pid] = [nx, ny]
            return nx, ny

def broadcast_positions(game_state):
    with game_state.lock:
        lines = []
        for pid, (x, y) in game_state.players.items():
            lines.append(f"POS {pid} {x} {y}")
        msg = "\n".join(lines) + "\n"

        dead = []
        for pid, conn in game_state.conns.items():
            try:
                conn.sendall(msg.encode())
            except OSError:
                dead.append(pid)

        for pid in dead:
            conn = game_state.conns.pop(pid, None)
            game_state.players.pop(pid, None)
            if conn is not None:
                try:
                    conn.close()
                except OSError:
                    pass



def handle_client(conn, addr, game_state):
    print("Client connected", addr)
    buf = b""
    pid = None

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buf += data

            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = line.decode().strip()

                if text == "JOIN" and pid is None:
                    pid, x, y = game_state.add_player()
                    with game_state.lock:
                        game_state.conns[pid] = conn

                    conn.sendall(f"WELCOME {pid}\n".encode())
                    conn.sendall(f"SPAWN {x} {y}\n".encode())

                    # send maze rows to this client
                    with game_state.lock:
                        for row in game_state.maze:
                            row_str = "".join(str(c) for c in row)
                            conn.sendall(f"MAZEROW {row_str}\n".encode())

                    broadcast_positions(game_state)


                elif text.startswith("MOVE") and pid is not None:
                    parts = text.split()
                    if len(parts) != 2:
                        continue
                    direction = parts[1]

                    dx, dy = 0, 0
                    if direction == "UP":
                        dx, dy = 0, -1
                    elif direction == "DOWN":
                      dx, dy = 0, 1
                    elif direction == "LEFT":
                        dx, dy = -1, 0
                    elif direction == "RIGHT":
                        dx, dy = 1, 0

                    x, y = game_state.move_player(pid, dx, dy)
                    broadcast_positions(game_state)

    finally:
        print("Client disconnected", addr)
        with game_state.lock:
            if pid in game_state.conns:
                del game_state.conns[pid]
            if pid in game_state.players:
                del game_state.players[pid]
        try:
            conn.close()
        except OSError:
            pass
        broadcast_positions(game_state)



def generate_maze(rows, cols):
    maze = [[1 for _ in range(cols)] for _ in range(rows)]

    def carve(x, y):
        directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 1 <= nx < cols-1 and 1 <= ny < rows-1 and maze[ny][nx] == 1:
                maze[y + dy//2][x + dx//2] = 0
                maze[ny][nx] = 0
                carve(nx, ny)

    maze[1][1] = 0
    carve(1, 1)

    # Set exit
    for ey in range(rows-2, 0, -1):
        for ex in range(cols-2, 0, -1):
            if maze[ey][ex] == 0:
                maze[ey][ex] = 2
                return maze
    maze[rows-2][cols-2] = 2
    return maze

def main():
    rows, cols = 21, 21
    maze = generate_maze(rows, cols)
    game_state = GameState(rows, cols, maze)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Game server listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr, game_state),
                daemon=True,
            ).start()



if __name__ == "__main__":
    main()
