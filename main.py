import pygame
import sys
import random
import time

pygame.init()

# Tile setup
TILE_SIZE = 20
TOP_MARGIN = 40    # Space for timer
BOTTOM_MARGIN = 30 # Space for restart instructions

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (70, 70, 70)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Player colors for multiple players
PLAYER_COLORS = {
    "me": BLUE,
    "p2": RED,
    "p3": YELLOW,
    "p4": (0, 255, 255),  # cyan
}

# Fonts
font = pygame.font.SysFont("Arial", 48)        # Safe font for win message
small_font = pygame.font.SysFont("Arial", 20)  # Timer, buttons, instructions

# Difficulty settings (ROWS, COLS)
DIFFICULTY_SIZES = {
    "Easy": (15, 20),
    "Medium": (24, 32),
    "Hard": (36, 50)
}

# Menu window size
MENU_WIDTH = 640
MENU_HEIGHT = 480
screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))

# Maze generation
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

# Draw maze with margins (no players here)
def draw_maze(maze):
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell == 1:
                color = GRAY
            elif cell == 2:
                color = GREEN
            else:
                color = WHITE
            pygame.draw.rect(
                screen,
                color,
                (x * TILE_SIZE, y * TILE_SIZE + TOP_MARGIN, TILE_SIZE, TILE_SIZE)
            )

# Display message
def show_message(text, color=RED):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
    screen.blit(surf, rect)
    pygame.display.flip()
    pygame.time.wait(1500)

# Menu
def show_menu():
    running = True
    selected = None
    buttons = []
    start_y = MENU_HEIGHT//2 - 60
    for i, diff in enumerate(DIFFICULTY_SIZES.keys()):
        rect = pygame.Rect(MENU_WIDTH//2 - 60, start_y + i*60, 120, 40)
        buttons.append((rect, diff))
    while running:
        screen.fill(BLACK)
        title = font.render("Select Difficulty", True, YELLOW)
        title_rect = title.get_rect(center=(MENU_WIDTH//2, 80))
        screen.blit(title, title_rect)

        mx, my = pygame.mouse.get_pos()
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = True

        for rect, diff in buttons:
            color = BLUE if rect.collidepoint((mx, my)) else WHITE
            pygame.draw.rect(screen, color, rect)
            txt = small_font.render(diff, True, BLACK)
            txt_rect = txt.get_rect(center=rect.center)
            screen.blit(txt, txt_rect)
            if rect.collidepoint((mx, my)) and click:
                selected = diff
                running = False

        pygame.display.flip()
    return selected

# Local game state for the client
class LocalGameState:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.maze = generate_maze(rows, cols)
        self.players = {}  # player_id -> [x, y]

    def set_player(self, player_id, x, y):
        self.players[player_id] = [x, y]

# Draw the whole world (maze + all players + UI)
def draw_world(screen, state, my_id, start_time, height):
    # 1) draw maze
    draw_maze(state.maze)

    # 2) draw every player
    for pid, (x, y) in state.players.items():
        color = PLAYER_COLORS.get(pid, BLUE)
        pygame.draw.rect(
            screen,
            color,
            (x * TILE_SIZE, y * TILE_SIZE + TOP_MARGIN, TILE_SIZE, TILE_SIZE)
        )

    # 3) timer at top-left
    elapsed_time = time.time() - start_time
    timer_text = small_font.render(f"Timer: {elapsed_time:.2f}s", True, WHITE)
    screen.blit(timer_text, (10, 10))

    # 4) restart instructions at bottom
    restart_text = small_font.render("Press R to restart maze", True, WHITE)
    screen.blit(restart_text, (10, height - 25))

# Update player position from input (local for now)
def handle_input(local_state, my_id):
    keys = pygame.key.get_pressed()
    dx, dy = 0, 0

    if keys[pygame.K_UP]:
        dy = -1
    elif keys[pygame.K_DOWN]:
        dy = 1
    elif keys[pygame.K_LEFT]:
        dx = -1
    elif keys[pygame.K_RIGHT]:
        dx = 1

    if dx != 0 or dy != 0:
        x, y = local_state.players[my_id]
        new_x, new_y = x + dx, y + dy

        # bounds check
        if 0 <= new_x < local_state.cols and 0 <= new_y < local_state.rows:
            # wall check (1 = wall)
            if local_state.maze[new_y][new_x] != 1:
                local_state.players[my_id] = [new_x, new_y]

# Main game
def main():
    global screen

    # Select difficulty
    difficulty = show_menu()
    ROWS, COLS = DIFFICULTY_SIZES[difficulty]

    # Adjust window size dynamically
    WIDTH = COLS * TILE_SIZE
    HEIGHT = ROWS * TILE_SIZE + TOP_MARGIN + BOTTOM_MARGIN
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # Create local game state
    state = LocalGameState(ROWS, COLS)
    my_id = "me"
    state.set_player(my_id, 1, 1)

    # Dummy second player to show multi-player rendering
    state.set_player("p2", 3, 1)

    clock = pygame.time.Clock()
    running = True
    won = False
    start_time = time.time()

    while running:
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # Restart maze
        if keys[pygame.K_r]:
            state = LocalGameState(ROWS, COLS)
            state.set_player(my_id, 1, 1)
            state.set_player("p2", 3, 1)
            won = False
            start_time = time.time()

        # Handle movement (for now: local only)
        handle_input(state, my_id)

        # Win check (only for my player)
        x, y = state.players[my_id]
        if state.maze[y][x] == 2 and not won:
            elapsed = time.time() - start_time
            draw_maze(state.maze)
            pygame.display.flip()
            show_message(f"You Win! Time: {elapsed:.2f}s", GREEN)
            won = True

        # Draw everything via draw_world
        draw_world(screen, state, my_id, start_time, HEIGHT)

        pygame.display.flip()
        clock.tick(15)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
