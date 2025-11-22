import socket
import threading
import random, time, statistics

HOST = "0.0.0.0"
PORT = 5001


class GameState:
    def __init__(self, rows, cols, maze, doors):
        self.rows = rows
        self.cols = cols
        self.maze = maze          # 2D list
        self.players = {}         # player_id -> [x, y]
        self.conns = {}           # player_id -> socket
        self.next_id = 1
        self.lock = threading.Lock()

        # door positions as a set of (x, y)
        self.doors = set(doors)

        # door position -> occupant player id or None
        self.door_occupant = {pos: None for pos in self.doors}

        # door position -> list of highlight tiles (including the door)
        self.door_highlights = {pos: [] for pos in self.doors}

    def add_player(self):
        # create a new player at starting position 1,1
        with self.lock:
            pid = f"p{self.next_id}"
            self.next_id += 1
            self.players[pid] = [1, 1]
            return pid, 1, 1

    def move_player(self, pid, dx, dy):
        """
        Move player and return
        (new_x, new_y, tile_updates)

        tile_updates is a list of (x, y, new_value) to send to clients.
        """
        with self.lock:
            x, y = self.players[pid]
            nx = x + dx
            ny = y + dy

            tile_updates = []

            # check bounds of maze
            if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                return x, y, tile_updates

            current_pos = (x, y)
            target_pos = (nx, ny)

            current_cell = self.maze[y][x]
            target_cell = self.maze[ny][nx]

            # is current or target a door position
            current_is_door = current_pos in self.doors
            target_is_door = target_pos in self.doors

            # helper to check if a door tile is free for this player
            def door_is_free(door_pos, player_id):
                if door_pos not in self.door_occupant:
                    return False
                occ = self.door_occupant[door_pos]
                if occ is None:
                    return True
                return occ == player_id

            # walls always block
            if target_cell == 1:
                return x, y, tile_updates

            # door logic
            if target_is_door:
                if not door_is_free(target_pos, pid):
                    # another player is inside this door area
                    return x, y, tile_updates

            # movement allowed
            self.players[pid] = [nx, ny]

            # if we left a door, and moved to a tile that is not the same door
            if current_is_door and current_pos != target_pos:
                # this player was inside this door
                if self.door_occupant.get(current_pos) == pid:
                    # clear highlights and remove the door completely
                    highlights = self.door_highlights.get(current_pos, [])
                    for hx, hy in highlights:
                        # return tiles to normal path
                        self.maze[hy][hx] = 0
                        tile_updates.append((hx, hy, 0))

                    # remove door data
                    self.door_occupant.pop(current_pos, None)
                    self.door_highlights.pop(current_pos, None)
                    if current_pos in self.doors:
                        self.doors.remove(current_pos)

            # if we entered a door
            if target_is_door:
                # if nobody was in it before, this is the first player
                if self.door_occupant[target_pos] is None:
                    self.door_occupant[target_pos] = pid

                    # compute up to three closest path tiles around the door
                    dxdy = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    highlights = [target_pos]  # include door tile itself

                    for ddx, ddy in dxdy:
                        if len(highlights) >= 4:  # door plus three paths
                            break
                        sx = nx + ddx
                        sy = ny + ddy
                        if 0 <= sx < self.cols and 0 <= sy < self.rows:
                            if self.maze[sy][sx] == 0:  # only path tiles
                                highlights.append((sx, sy))

                    # store highlights for this door
                    self.door_highlights[target_pos] = highlights

                    # mark them as red tiles (value 4) in maze
                    for hx, hy in highlights:
                        self.maze[hy][hx] = 4
                        tile_updates.append((hx, hy, 4))

                else:
                    # door already in use by same player, do nothing special
                    pass

            return nx, ny, tile_updates


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


def broadcast_tile(game_state, x, y, value):
    msg = f"TILE {x} {y} {value}\n"
    with game_state.lock:
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

                    _, _, tile_updates = game_state.move_player(pid, dx, dy)

                    # send tile updates to all clients
                    for tx, ty, val in tile_updates:
                        broadcast_tile(game_state, tx, ty, val)

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
    """
    Large maze with limited loops, one exit, and static doors.

    0 = path
    1 = wall
    2 = exit
    3 = door location (before any player uses it)
    4 = red highlight tiles (door plus nearby paths while in use)
    """

    # start with all walls
    maze = [[1 for _ in range(cols)] for _ in range(rows)]

    def in_bounds(r, c):
        return 1 <= r < rows - 1 and 1 <= c < cols - 1

    def shuffled_dirs():
        dirs = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        random.shuffle(dirs)
        return dirs

    # depth first search to carve a perfect maze
    start_r, start_c = 1, 1
    maze[start_r][start_c] = 0
    stack = [(start_r, start_c)]

    while stack:
        r, c = stack[-1]
        carved = False

        for dr, dc in shuffled_dirs():
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and maze[nr][nc] == 1:
                wall_r = r + dr // 2
                wall_c = c + dc // 2
                maze[wall_r][wall_c] = 0
                maze[nr][nc] = 0
                stack.append((nr, nc))
                carved = True
                break

        if not carved:
            stack.pop()

    # limited loops so only a few alternate paths exist
    MAX_LOOPS = 5
    loops_added = 0
    attempts = rows * cols

    while loops_added < MAX_LOOPS and attempts > 0:
        attempts -= 1

        x = random.randrange(1, cols - 1)
        y = random.randrange(1, rows - 1)

        if maze[y][x] != 1:
            continue

        vertical_corridor = (maze[y - 1][x] == 0 and maze[y + 1][x] == 0)
        horizontal_corridor = (maze[y][x - 1] == 0 and maze[y][x + 1] == 0)

        if vertical_corridor or horizontal_corridor:
            maze[y][x] = 0
            loops_added += 1

    # choose exit near the bottom right among path cells
    exit_pos = None
    for ey in range(rows - 2, 0, -1):
        for ex in range(cols - 2, 0, -1):
            if maze[ey][ex] == 0:
                maze[ey][ex] = 2
                exit_pos = (ex, ey)
                break
        if exit_pos is not None:
            break

    if exit_pos is None:
        maze[rows - 2][cols - 2] = 2
        exit_pos = (cols - 2, rows - 2)

    # place some doors on corridors
    doors = []
    DOOR_COUNT = 6  # number of shared door objects (independent of path count)

    attempts = rows * cols
    while len(doors) < DOOR_COUNT and attempts > 0:
        attempts -= 1
        x = random.randrange(1, cols - 1)
        y = random.randrange(1, rows - 1)

        if maze[y][x] != 0:
            continue

        # do not place doors on start or exit
        if (x, y) == (1, 1) or (x, y) == exit_pos:
            continue

        # only place doors in straight corridors
        neighbors = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ]
        open_neighbors = sum(
            1 for nx, ny in neighbors
            if 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] in (0, 2)
        )

        if open_neighbors == 2:
            maze[y][x] = 3
            doors.append((x, y))

    return maze, doors


def main():
    rows, cols = 51, 51
    maze, doors = generate_maze(rows, cols)
    game_state = GameState(rows, cols, maze, doors)

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
