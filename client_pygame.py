import socket
import pygame

HOST = "192.168.9.125"
PORT = 5001

WINDOW_SIZE = 790           # square window
TILE_SIZE = None            # we will compute this after we know maze size

BACKGROUND_COLOR = (0, 0, 0)
MY_COLOR = (0, 200, 0)
OTHER_COLOR = (200, 0, 0)
WALL_COLOR = (80, 80, 80)
EXIT_COLOR = (0, 0, 200)   # blue for the exit
DOOR_COLOR = (160, 110, 40)   # brown-ish for doors
HIGHLIGHT_COLOR = (255, 0, 0)   # red tiles from shared doors


def main():
    global TILE_SIZE

    # connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.sendall(b"JOIN\n")
    sock.settimeout(0.01)

    positions = {}
    my_pid = None

    maze_rows = []
    maze = None

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Maze multiplayer")
    clock = pygame.time.Clock()

    running = True

    while running:
        # handle input events
        move_cmd = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    move_cmd = b"MOVE UP\n"
                elif event.key == pygame.K_s:
                    move_cmd = b"MOVE DOWN\n"
                elif event.key == pygame.K_a:
                    move_cmd = b"MOVE LEFT\n"
                elif event.key == pygame.K_d:
                    move_cmd = b"MOVE RIGHT\n"

        if move_cmd is not None:
            sock.sendall(move_cmd)

        # receive messages from server
        try:
            data = sock.recv(4096)
        except socket.timeout:
            data = b""

        if data:
            text = data.decode().strip()
            for line in text.split("\n"):
                if not line:
                    continue

                if line.startswith("WELCOME"):
                    _, my_pid = line.split()
                    print("My player id:", my_pid)

                elif line.startswith("SPAWN"):
                    parts = line.split()
                    if len(parts) == 3 and my_pid is not None:
                        x = int(parts[1])
                        y = int(parts[2])
                        positions[my_pid] = (x, y)

                elif line.startswith("TILE"):
                    parts = line.split()
                    if len(parts) == 4 and maze is not None:
                        x = int(parts[1])
                        y = int(parts[2])
                        v = int(parts[3])
                        if 0 <= y < len(maze) and 0 <= x < len(maze[0]):
                            maze[y][x] = v

                elif line.startswith("MAZEROW"):
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        row_str = parts[1]
                        maze_rows.append([int(ch) for ch in row_str])
                        # update maze as rows arrive
                        maze = maze_rows

                elif line.startswith("POS"):
                    parts = line.split()
                    if len(parts) == 4:
                        _, pid_msg, x_str, y_str = parts
                        positions[pid_msg] = (int(x_str), int(y_str))

        # if we have the maze and tile size is not set yet, compute it
        if maze is not None and TILE_SIZE is None:
            rows = len(maze)
            cols = len(maze[0])
            TILE_SIZE = min(WINDOW_SIZE // cols, WINDOW_SIZE // rows)
            # just to be safe, make it at least 6 pixels
            TILE_SIZE = max(TILE_SIZE, 6)
            print("Maze size:", rows, "x", cols, "Tile:", TILE_SIZE)

        screen.fill(BACKGROUND_COLOR)

        # draw maze tiles
        if maze is not None and TILE_SIZE is not None:
            rows = len(maze)
            cols = len(maze[0])

            for y in range(rows):
                for x in range(cols):
                    cell = maze[y][x]
                    if cell == 1:   # wall
                        rect = pygame.Rect(
                            x * TILE_SIZE,
                            y * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                        )
                        pygame.draw.rect(screen, WALL_COLOR, rect)
                    elif cell == 2:  # exit
                        rect = pygame.Rect(
                            x * TILE_SIZE,
                            y * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                        )
                        pygame.draw.rect(screen, EXIT_COLOR, rect)
                    elif cell == 3:  # door
                        rect = pygame.Rect(
                            x * TILE_SIZE,
                            y * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                        )
                        pygame.draw.rect(screen, DOOR_COLOR, rect)
                    elif cell == 4:  # highlight from shared door
                        rect = pygame.Rect(
                            x * TILE_SIZE,
                            y * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                        )
                        pygame.draw.rect(screen, HIGHLIGHT_COLOR, rect)

        # draw players
        if TILE_SIZE is not None:
            for pid, (x, y) in positions.items():
                color = MY_COLOR if pid == my_pid else OTHER_COLOR
                rect = pygame.Rect(
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(screen, color, rect)

        pygame.display.flip()
        clock.tick(30)

    sock.close()
    pygame.quit()


if __name__ == "__main__":
    main()
