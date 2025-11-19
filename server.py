# server.py

import socket
import threading
import random

# you can copy your generate_maze from main.py into here too

class GameState:
    def __init__(self, rows, cols, maze):
        self.rows = rows
        self.cols = cols
        self.maze = maze          # 2D list
        self.players = {}         # player_id -> [x, y]
        self.next_id = 1

    def add_player(self):
        pid = f"p{self.next_id}"
        self.next_id += 1
        self.players[pid] = [1, 1]
        return pid, 1, 1

    def move_player(self, pid, dx, dy):
        # TODO: your bounds + wall checks here (similar to handle_input)
        pass


def handle_client(conn, addr, game_state):
    # 1. read JOIN line
    # 2. create player in game_state
    # 3. send WELCOME + MAZE + SPAWN
    # 4. loop:
    #       read lines
    #       if MOVE -> game_state.move_player(...)
    #                -> send POS to all clients
    pass

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
    generate_maze(21, 21)
    # TODO:
    # - generate maze
    # - create GameState
    # - create listening socket
    # - accept clients and start a thread with handle_client
    pass


if __name__ == "__main__":
    main()
