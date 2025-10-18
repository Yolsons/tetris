import pygame
import random

pygame.init()



# Размеры окна и игрового поля
GRID_SIZE = 30
COLUMNS, ROWS = 10, 20
WIDTH, HEIGHT = COLUMNS * GRID_SIZE, ROWS * GRID_SIZE
INFO_PANEL_WIDTH = 150  # Дополнительная панель справа
SCREEN_WIDTH = WIDTH + INFO_PANEL_WIDTH

# Цвета фигур
COLOR_MAP = {
    "I": (0, 255, 255),
    "J": (0, 0, 255),
    "L": (255, 165, 0),
    "O": (255, 255, 0),
    "S": (0, 255, 0),
    "T": (128, 0, 128),
    "Z": (255, 0, 0),
}

# Фигуры тетриса
SHAPES = {
    "I": [[1, 1, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "Z": [[1, 1, 0], [0, 1, 1]],
}

screen = pygame.display.set_mode((SCREEN_WIDTH, HEIGHT))
pygame.display.set_caption("Tetris")

grid = [[(0, 0, 0) for _ in range(COLUMNS)] for _ in range(ROWS)]
font = pygame.font.Font(None, 36)

class Piece:
    def __init__(self, shape_name):
        self.shape_name = shape_name
        self.shape = SHAPES[shape_name]
        self.color = COLOR_MAP[shape_name]
        self.x = COLUMNS // 2 - len(self.shape[0]) // 2
        self.y = 0

    def move_down(self):
        self.y += 1
        if self.check_collision():
            self.y -= 1
            self.lock_piece()
            return True
        return False

    def hard_drop(self):
        while not self.move_down():
            pass

    def rotate(self):
        old_shape = self.shape
        self.shape = [list(row) for row in zip(*self.shape[::-1])]
        if self.check_collision():
            self.shape = old_shape

    def check_collision(self):
        for i, row in enumerate(self.shape):
            for j, cell in enumerate(row):
                if cell:
                    new_x = self.x + j
                    new_y = self.y + i
                    if new_x < 0 or new_x >= COLUMNS or new_y >= ROWS:
                        return True
                    if grid[new_y][new_x] != (0, 0, 0):
                        return True
        return False

    def move(self, dx):
        self.x += dx
        if self.check_collision():
            self.x -= dx

    def lock_piece(self):
        for i, row in enumerate(self.shape):
            for j, cell in enumerate(row):
                if cell:
                    grid[self.y + i][self.x + j] = self.color
        if self.y <= 0:
            game_over()
        clear_rows()
        new_piece()

def clear_rows():
    global grid, score
    full_rows = [i for i in range(ROWS) if all(grid[i][j] != (0, 0, 0) for j in range(COLUMNS))]
    
    if full_rows:
        points = {1: 10, 2: 15, 3: 25, 4: 40}
        score += points.get(len(full_rows), 0)

        for row in full_rows:
            del grid[row]
            grid.insert(0, [(0, 0, 0) for _ in range(COLUMNS)])

def new_piece():
    global current_piece
    current_piece = Piece(random.choice(list(SHAPES.keys())))

def game_over():
    global running, game_over_screen
    game_over_screen = True

def restart_game():
    global grid, score, game_over_screen, running
    grid = [[(0, 0, 0) for _ in range(COLUMNS)] for _ in range(ROWS)]
    score = 0
    game_over_screen = False
    new_piece()

current_piece = Piece(random.choice(list(SHAPES.keys())))
score = 0
fall_time = 0
fall_speed = 500
clock = pygame.time.Clock()
running = True
game_over_screen = False

move_left = move_right = False
move_timer = 0

while running:
    screen.fill((0, 0, 0))
    time_passed = clock.tick(60)
    fall_time += time_passed
    move_timer += time_passed

    if not game_over_screen:
        if fall_time > fall_speed:
            if current_piece.move_down():
                new_piece()
            fall_time = 0

        if move_timer > 50:  # Плавное движение
            if move_left:
                current_piece.move(-1)
            if move_right:
                current_piece.move(1)
            move_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    move_left = True
                elif event.key == pygame.K_RIGHT:
                    move_right = True
                elif event.key == pygame.K_DOWN:
                    current_piece.move_down()
                elif event.key in (pygame.K_UP, pygame.K_DOWN):
                    current_piece.rotate()
                elif event.key == pygame.K_SPACE:
                    current_piece.hard_drop()
                    new_piece()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    move_left = False
                elif event.key == pygame.K_RIGHT:
                    move_right = False
    else:
        screen.fill((30, 30, 30))
        text = font.render("GAME OVER", True, (255, 0, 0))
        restart_text = font.render("Press ENTER to restart", True, (255, 255, 255))
        screen.blit(text, (WIDTH // 2 - 60, HEIGHT // 2 - 20))
        screen.blit(restart_text, (WIDTH // 2 - 100, HEIGHT // 2 + 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                restart_game()

    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

    for i, row in enumerate(grid):
        for j, color in enumerate(row):
            if color != (0, 0, 0):
                pygame.draw.rect(screen, color, (j * GRID_SIZE, i * GRID_SIZE, GRID_SIZE, GRID_SIZE))
                pygame.draw.rect(screen, (255, 255, 255), (j * GRID_SIZE, i * GRID_SIZE, GRID_SIZE, GRID_SIZE), 2)

    for i, row in enumerate(current_piece.shape):
        for j, cell in enumerate(row):
            if cell:
                x, y = (current_piece.x + j) * GRID_SIZE, (current_piece.y + i) * GRID_SIZE
                pygame.draw.rect(screen, current_piece.color, (x, y, GRID_SIZE, GRID_SIZE))
                pygame.draw.rect(screen, (255, 255, 255), (x, y, GRID_SIZE, GRID_SIZE), 2)

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (WIDTH + 10, 20))

    pygame.display.flip()

pygame.quit()

