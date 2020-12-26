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


def load_sound(name):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с музыкой '{fullname}' не найден")
        sys.exit()
    soundtrack = pygame.mixer.Sound(fullname)
    pygame.mixer.music.load(fullname)
    pygame.mixer.music.set_volume(0.05)
    return soundtrack


class Game:
    def __init__(self):
        pygame.display.set_caption('Морской бой')
        self.clock = pygame.time.Clock()
        self.ship_group = pygame.sprite.Group()
        self.background = Background()

        self.scenes = [self.background.begin_scene,
                       self.background.begin_scene,
                       self.background.placement_of_ships_scene,
                       self.background.battle_scene]
        self.scenes_idx = 0

    def game_loop(self):
        self.scenes[self.scenes_idx](0)
        load_sound('soundtrack.wav')
        pygame.mixer.music.play(loops=-1)
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.scenes_idx == 0 and \
                        140 <= event.pos[0] <= 370 and 350 <= event.pos[1] <= 430:
                    self.scenes_idx += 1
                    self.scenes[self.scenes_idx](self.scenes_idx)
                elif self.scenes_idx == 1 and event.type == pygame.MOUSEBUTTONDOWN and \
                        140 <= event.pos[0] <= 390 and (300 <= event.pos[1] <= 380 or
                                                        400 <= event.pos[1] <= 480):
                    if 300 <= event.pos[1] <= 380:
                        self.mode = 'Робот'
                    else:
                        self.mode = '2 игрока'
                    self.scenes_idx += 1
                    self.scenes[self.scenes_idx]()
                    self.ships = [Ship(self.ship_group, 'single', 540, 210), Ship(self.ship_group, 'single', 600, 210),
                                  Ship(self.ship_group, 'single', 660, 210), Ship(self.ship_group, 'single', 720, 210),
                                  Ship(self.ship_group, 'double', 540, 270), Ship(self.ship_group, 'double', 630, 270),
                                  Ship(self.ship_group, 'double', 720, 270), Ship(self.ship_group, 'third', 540, 330),
                                  Ship(self.ship_group, 'third', 660, 330), Ship(self.ship_group, 'forth', 540, 390)]
                elif self.scenes_idx == 2 and event.type == pygame.MOUSEBUTTONDOWN and \
                        80 <= event.pos[0] <= 160 and 80 <= event.pos[1] <= 130:
                    self.scenes_idx -= 1
                    self.scenes[self.scenes_idx](self.scenes_idx)
                    self.ship_group.empty()

            self.ship_group.draw(screen)
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


class Ship(pygame.sprite.Sprite):
    def __init__(self, group, type, x, y):
        super().__init__(group)
        self.image = load_image(f"{type}-deck ship.png")
        self.type = type
        self.state = 'stable'
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

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

    def draw_field(self, coord):
        # (60, 100, 35)
        # (450, 490, 755)
        pygame.draw.rect(screen, 'blue', (shift + coord[0], shift + 150, 300, 300), 3)
        font = pygame.font.Font(None, 30)
        for i in range(1, 11):
            text = font.render(str(i), True, (0, 0, 255))
            if i == 10:
                screen.blit(text, (i * cell_size + coord[1] - 5,
                                   4 * cell_size + shift + 5))
            else:
                screen.blit(text, (i * cell_size + coord[1],
                                   4 * cell_size + shift + 5))
        string = 'абвгдеёжзи'
        for i in range(10):
            text = font.render(string[i], True, (0, 0, 255))
            if i == 4 or i == 7:
                screen.blit(text, (shift + 5 + coord[2] - 2,
                                   (5 + i) * cell_size + shift + 5))
            else:
                screen.blit(text, (shift + 5 + coord[2],
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
        screen.blit(load_image("background.jpg"), (0, 0))
        self.draw_background()
        self.draw_field((60, 100, 35))

        font = pygame.font.SysFont("Segoe Print", 30)
        text = font.render("Далее", True, (0, 0, 255))
        screen.blit(text, (720, 465))
        pygame.draw.rect(screen, (0, 0, 255), (710, 470, 115, 50), 5)

        text = font.render("Авто", True, (0, 0, 255))
        screen.blit(text, (570, 465))
        pygame.draw.rect(screen, (0, 0, 255), (560, 470, 110, 50), 5)

        screen.blit(load_image("reset.png"), (450, 450))
        pygame.draw.rect(screen, (0, 0, 255), (440, 440, 80, 80), 5)

        pygame.draw.polygon(screen, (0, 0, 255), ((120, 90), (90, 105), (120, 120)))
        pygame.draw.rect(screen, (0, 0, 255), (120, 100, 30, 10))
        pygame.draw.rect(screen, (0, 0, 255), (80, 80, 80, 50), 5)

    def battle_scene(self):
        pass

    def result_scene(self):
        pass


def main():
    if __name__ == '__main__':
        game = Game()
        game.game_loop()
        pygame.quit()


main()
