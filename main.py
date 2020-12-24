import pygame
import os
import sys

pygame.init()
size = width, height = 930, 600
screen = pygame.display.set_mode(size)
shift = 60
cell_size = 30


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Game:
    def __init__(self):
        pygame.display.set_caption('Морской бой')
        self.clock = pygame.time.Clock()
        self.all_sprites = pygame.sprite.Group()
        self.background = Background()
        self.scenes = [self.background.begin_scene,
                       self.background.begin_scene,
                       self.background.placement_of_ships_scene,
                       self.background.battle_scene]
        self.scenes_idx = 0

    def game_loop(self):
        self.scenes[self.scenes_idx](0)
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.scenes_idx == 0 and \
                        140 <= event.pos[0] <= 370 and 350 <= event.pos[1] <= 430:
                    self.scenes_idx += 1
                    self.scenes[self.scenes_idx](self.scenes_idx)
                elif self.scenes_idx == 1 and event.type == pygame.MOUSEBUTTONDOWN:
                    if 140 <= event.pos[0] <= 390 and 300 <= event.pos[1] <= 380:
                        self.mode = 'Робот'
                        self.scenes_idx += 1
                        self.scenes[self.scenes_idx]()
                        print(self.mode)
                    elif 140 <= event.pos[0] <= 390 and 400 <= event.pos[1] <= 480:
                        self.mode = '2 игрока'
                        self.scenes_idx += 1
                        self.scenes[self.scenes_idx]()
                        print(self.mode)
            self.all_sprites.draw(screen)
            pygame.display.flip()

    def robot_move(self):
        pass

    def player_move(self):
        pass


class GameField:
    def __init__(self):
        self.field = [[0 for j in range(10)] for i in range(10)]

    def make_move(self, coords):
        pass


class Ship:
    def __init__(self, type):
        self.type = type
        self.state = 'stable'

    def get_type(self):
        return self.type

    def get_state(self):
        return self.state


class Background:
    def draw_background(self):
        pygame.draw.rect(screen, 'white', (shift, shift, 810, 480))
        for i in range(0, 810, cell_size):
            for j in range(0, 480, cell_size):
                pygame.draw.rect(screen, (135, 206, 235),
                                 (i + shift, j + shift,
                                  cell_size, cell_size), 2)
        pygame.draw.line(screen, 'red', (shift, shift + 90),
                         (shift + 810, shift + 90), 3)

    def draw_fields(self):
        for i in [60, 450]:
            pygame.draw.rect(screen, 'blue', (shift + i, shift + 150, 300, 300), 3)
        font = pygame.font.Font(None, 30)
        for j in [100, 490]:
            for i in range(1, 11):
                text = font.render(str(i), True, (0, 0, 255))
                if i == 10:
                    screen.blit(text, (i * cell_size + j - 5,
                                       4 * cell_size + shift + 5))
                else:
                    screen.blit(text, (i * cell_size + j,
                                       4 * cell_size + shift + 5))
        string = 'абвгдеёжзи'
        for j in [35, 755]:
            for i in range(10):
                text = font.render(string[i], True, (0, 0, 255))
                if i == 4 or i == 7:
                    screen.blit(text, (shift + 5 + j - 2,
                                       (5 + i) * cell_size + shift + 5))
                else:
                    screen.blit(text, (shift + 5 + j,
                                       (5 + i) * cell_size + shift + 5))

    def begin_scene(self, num_scene):
        screen.blit(load_image("background.jpg"), (0, 0))
        self.draw_background()
        screen.blit(load_image("menu_picture.png"), (450, 210))
        screen.blit(load_image("pen.png"), (600, -30))

        font = pygame.font.SysFont("Segoe Print", 50)
        if num_scene == 0:
            text = font.render("Играть", True, (0, 0, 255))
            screen.blit(text, (150, 340))
            pygame.draw.rect(screen, (0, 0, 255), (140, 350, 230, 80), 5)
        else:
            text = font.render("Робот", True, (0, 0, 255))
            screen.blit(text, (180, 290))
            pygame.draw.rect(screen, (0, 0, 255), (140, 300, 250, 80), 5)

            text = font.render("2 игрока", True, (0, 0, 255))
            screen.blit(text, (150, 390))
            pygame.draw.rect(screen, (0, 0, 255), (140, 400, 250, 80), 5)

        font.set_bold(True)
        text = font.render("Морской бой", True, (0, 0, 255))
        screen.blit(text, (80, 180))

    def placement_of_ships_scene(self):
        pass

    def battle_scene(self):
        pass


def main():
    if __name__ == '__main__':
        game = Game()
        game.game_loop()
        pygame.quit()


main()
