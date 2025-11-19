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
        self.next_id = 1
        self.lock = threading.Lock()

    def add_player(self):
        with self.lock:
            pid = f"p{self.next_id}"
            self.next_id += 1
            self.players[pid] = [1, 1]
            return pid, 1, 1

    def move_player(self, pid, dx, dy):
        with self.lock:
            x, y = self.players[pid]
            nx = x + dx
            ny = y + dy

            if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                return x, y

            cell = self.maze[ny][nx]
            if cell == 1:
                return x, y

            self.players[pid] = [nx, ny]
            return nx, ny



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
                    conn.sendall(f"WELCOME {pid}\n".encode())
                    conn.sendall(f"SPAWN {x} {y}\n".encode())

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
                    conn.sendall(f"POS {x} {y}\n".encode())

    finally:
        print("Client disconnected", addr)
        conn.close()


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
