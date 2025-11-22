import socket
import pygame

HOST = "192.168.9.125"
PORT = 5001

TILE_SIZE = 32
ROWS = 21
COLS = 21

BACKGROUND_COLOR = (0, 0, 0)
MY_COLOR = (0, 200, 0)
OTHER_COLOR = (200, 0, 0)
WALL_COLOR = (80, 80, 80)



def main():
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
    screen = pygame.display.set_mode((COLS * TILE_SIZE, ROWS * TILE_SIZE))
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
                elif line.startswith("MAZEROW"):
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        row_str = parts[1]
                        maze_rows.append([int(ch) for ch in row_str])
                        if len(maze_rows) == ROWS:
                            maze = maze_rows
                elif line.startswith("POS"):
                    parts = line.split()
                    if len(parts) == 4:
                        _, pid_msg, x_str, y_str = parts
                        positions[pid_msg] = (int(x_str), int(y_str))


        screen.fill(BACKGROUND_COLOR)

        # draw maze walls
        if maze is not None:
            for y in range(ROWS):
                for x in range(COLS):
                    if maze[y][x] == 1:
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(screen, WALL_COLOR, rect)

        # draw players
        for pid, (x, y) in positions.items():
            if pid == my_pid:
                color = MY_COLOR
            else:
                color = OTHER_COLOR
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, color, rect)


        pygame.display.flip()
        clock.tick(30)

    sock.close()
    pygame.quit()


if __name__ == "__main__":
    main()
