import pygame
import random

# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 300, 600
BLOCK_SIZE = 30
COLUMNS, ROWS = WIDTH // BLOCK_SIZE, HEIGHT // BLOCK_SIZE

# Цвета фигур
COLORS = [
    (0, 255, 255),  # Голубой
    (0, 0, 255),    # Синий
    (255, 165, 0),  # Оранжевый
    (255, 255, 0),  # Желтый
    (0, 255, 0),    # Зеленый
    (128, 0, 128),  # Фиолетовый
    (255, 0, 0)     # Красный
]

# Фигуры тетриса
SHAPES = [
    [[1, 1, 1, 1]],  # I-фигура
    [[1, 1, 1],
     [0, 1, 0]],     # T-фигура
    [[1, 1, 1],
     [1, 0, 0]],     # L-фигура
    [[1, 1, 1],
     [0, 0, 1]],     # J-фигура
    [[1, 1],
     [1, 1]],        # O-фигура
    [[0, 1, 1],
     [1, 1, 0]],     # S-фигура
    [[1, 1, 0],
     [0, 1, 1]]      # Z-фигура
]

# Игровое окно
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris")

# Функция для рисования сетки
def draw_grid():
    for x in range(0, WIDTH, BLOCK_SIZE):
        pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, BLOCK_SIZE):
        pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

# Основной игровой цикл
running = True
while running:
    screen.fill((0, 0, 0))
    draw_grid()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
