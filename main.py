import pygame
import os
import sys
from random import randint, choice, shuffle
from time import sleep

pygame.init()
SIZE = 930, 600
SCREEN = pygame.display.set_mode(SIZE)
SHIFT = 60
CELL_SIZE = 30

ship_groups = [pygame.sprite.Group(), pygame.sprite.Group()]
shell_group = pygame.sprite.Group()
cross_group = pygame.sprite.Group()
visible_ships = pygame.sprite.Group()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', 'images', name)
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
    fullname = os.path.join('data', 'music', name)
    if not os.path.isfile(fullname):
        print(f"Файл с музыкой '{fullname}' не найден")
        sys.exit()
    return fullname


class Game:
    def __init__(self):
        pygame.display.set_caption('Морской бой')
        self.clock = pygame.time.Clock()

        self.background = Background()

        self.scenes = [self.background.begin_scene,
                       self.background.begin_scene,
                       self.background.placement_of_ships_scene,
                       self.background.battle_scene,
                       self.background.result_scene]
        self.scenes_idx = 0

        self.selected_ship = None
        self.last_selected_ship = None

        self.fields = [GameField(), GameField()]
        self.field_idx = 0

        self.flag_ship_group1 = False
        self.flag_ship_group2 = False

        self.targets = None
        self.targets_idx = None

        self.winning_sound = pygame.mixer.Sound(load_sound('winning.wav'))
        self.defeat_sound = pygame.mixer.Sound(load_sound('defeat.wav'))

    def game_loop(self):
        self.scenes[self.scenes_idx](0)

        pygame.mixer.music.load(load_sound('soundtrack.wav'))
        pygame.mixer.music.set_volume(0.03)
        pygame.mixer.music.play(loops=-1)

        running = True
        while running:
            for event in pygame.event.get():
                # выход
                if event.type == pygame.QUIT:
                    running = False

                # кнопка "играть"
                elif event.type == pygame.MOUSEBUTTONDOWN and self.scenes_idx == 0 and \
                        140 <= event.pos[0] <= 370 and 350 <= event.pos[1] <= 430:
                    self.scenes_idx += 1
                    self.scenes[self.scenes_idx](self.scenes_idx)

                # выбор режима: "Робот" или "2 игрока"
                elif self.scenes_idx == 1 and event.type == pygame.MOUSEBUTTONDOWN and \
                        140 <= event.pos[0] <= 390 and (300 <= event.pos[1] <= 380 or
                                                        400 <= event.pos[1] <= 480):
                    if 300 <= event.pos[1] <= 380:
                        self.mode = 'Робот'
                    else:
                        self.mode = '2 игрока'

                    self.scenes_idx += 1
                    self.scenes[self.scenes_idx]()
                    self.init_ships(ship_groups[0])
                    self.init_ships(ship_groups[1])
                    self.flag_ship_group1 = True

                # кнопка "Назад"
                elif event.type == pygame.MOUSEBUTTONDOWN and \
                        (self.scenes_idx == 4 or (self.scenes_idx in [2, 3] and
                                                  80 <= event.pos[0] <= 160 and 80 <= event.pos[1] <= 130)):
                    self.scenes_idx = 1
                    self.field_idx = 0
                    self.fields = [GameField(), GameField()]
                    self.scenes[self.scenes_idx](self.scenes_idx)
                    for i in ship_groups:
                        i.empty()
                    shell_group.empty()
                    cross_group.empty()
                    visible_ships.empty()
                    self.flag_ship_group1 = False
                    self.flag_ship_group2 = False

                # кнопка "поворот"
                elif event.type == pygame.MOUSEBUTTONDOWN and self.scenes_idx == 2 and self.last_selected_ship and\
                        450 <= event.pos[0] <= 510 and 450 <= event.pos[1] <= 510 and \
                        self.last_selected_ship.type != 'single':
                    self.last_selected_ship.rotate()
                    if not self.last_selected_ship.correct_coords(ship_groups[self.field_idx].sprites()):
                        self.last_selected_ship.rotate()

                # кнопка "Авто"
                elif self.scenes_idx == 2 and event.type == pygame.MOUSEBUTTONDOWN and \
                        560 <= event.pos[0] <= 670 and 470 <= event.pos[1] <= 520:
                    self.fields[self.field_idx].generate_random_field(ship_groups[self.field_idx].sprites())

                # кнопка "Далее"
                elif self.scenes_idx == 2 and event.type == pygame.MOUSEBUTTONDOWN and \
                        710 <= event.pos[0] <= 825 and 470 <= event.pos[1] <= 520 and \
                        not [1 for i in ship_groups[self.field_idx].sprites()
                             if not pygame.Rect(SHIFT + 60, SHIFT + 150, 300, 300).contains(i.rect)]:
                    if self.mode == 'Робот':
                        self.fields[self.field_idx].generate_random_field(
                            ship_groups[self.field_idx + 1].sprites())

                    if self.mode == 'Робот' or self.field_idx == 1:
                        for i in range(len(self.fields)):
                            self.fields[i].set_field(ship_groups[i].sprites())
                        for i in ship_groups[1].sprites():
                            i.rect.x += 390

                        self.flag_ship_group1 = self.flag_ship_group2 = False
                        if self.mode == 'Робот':
                            visible_ships.add(ship_groups[0].sprites())

                        self.field_idx = -1
                        self.scenes_idx += 1
                        self.scenes[self.scenes_idx](self.mode, self.field_idx)
                    else:
                        self.scenes[self.scenes_idx]()
                        self.flag_ship_group1 = False
                        self.flag_ship_group2 = True
                    self.field_idx += 1

                # взятие корабля
                elif self.scenes_idx == 2 and event.type == pygame.MOUSEBUTTONDOWN:
                    result = [i for i in ship_groups[self.field_idx].sprites()
                              if i.rect.collidepoint(*event.pos)]
                    if result:
                        self.selected_ship = result[0]

                # перемещение корабля
                elif self.scenes_idx == 2 and event.type == pygame.MOUSEMOTION and self.selected_ship:
                    self.selected_ship.rect.x = event.pos[0]
                    self.selected_ship.rect.y = event.pos[1]

                # отпускание корабля
                elif self.scenes_idx == 2 and event.type == pygame.MOUSEBUTTONUP and self.selected_ship:
                    self.selected_ship.rect.x = event.pos[0] // CELL_SIZE * CELL_SIZE
                    self.selected_ship.rect.y = event.pos[1] // CELL_SIZE * CELL_SIZE
                    if self.selected_ship.correct_coords(ship_groups[self.field_idx].sprites()):
                        self.selected_ship.prev_coords = self.selected_ship.rect.x, self.selected_ship.rect.y
                    else:
                        if not pygame.Rect(SHIFT + 60, SHIFT + 150, 300, 300).contains(self.selected_ship.rect) and \
                                self.selected_ship.angle == -90:
                            self.selected_ship.rotate()

                        self.selected_ship.rect.x = self.selected_ship.prev_coords[0]
                        self.selected_ship.rect.y = self.selected_ship.prev_coords[1]
                    self.last_selected_ship = self.selected_ship
                    self.selected_ship = None

                elif self.scenes_idx == 3 and event.type == pygame.MOUSEBUTTONDOWN and self.mode == '2 игрока' and \
                        ((not self.field_idx and 510 <= event.pos[0] < 810) or
                         (self.field_idx and 120 <= event.pos[0] < 420)) and 210 <= event.pos[1] < 510 and \
                        not self.player_move(event.pos):
                    self.two_players_game_check()
                    self.field_idx = abs(self.field_idx - 1)

                elif self.scenes_idx == 3 and event.type == pygame.MOUSEBUTTONDOWN and self.mode == 'Робот' and \
                        510 <= event.pos[0] < 810 and 210 <= event.pos[1] < 510 and not self.player_move(event.pos):
                    self.robot_game_check()
                    self.robot_move()
                    self.robot_game_check()

            SCREEN.fill(0)

            if self.scenes_idx < 2:
                self.scenes[self.scenes_idx](self.scenes_idx)
            elif self.scenes_idx == 3:
                self.scenes[self.scenes_idx](self.mode, self.field_idx)
                visible_ships.draw(SCREEN)
                shell_group.draw(SCREEN)
                cross_group.draw(SCREEN)
            elif self.scenes_idx == 4:
                self.scenes[self.scenes_idx](self.result)
            else:
                self.scenes[self.scenes_idx]()

            if self.flag_ship_group1:
                ship_groups[0].draw(SCREEN)
            if self.flag_ship_group2:
                ship_groups[1].draw(SCREEN)

            pygame.display.flip()

    def init_ships(self, group):
        for i in [['single', 540, 210], ['single', 600, 210], ['single', 660, 210], ['single', 720, 210],
                  ['double', 540, 270], ['double', 630, 270], ['double', 720, 270], ['third', 540, 330],
                  ['third', 660, 330], ['forth', 540, 390]]:
            Ship(group, *i)

    def robot_move(self):
        i, j = randint(0, 9), randint(0, 9)
        while self.fields[0].field[i][j] == 'not available':
            i, j = randint(0, 9), randint(0, 9)
        self.fields[0].make_move(i, j, (j * CELL_SIZE + 120, i * CELL_SIZE + 210), self.field_idx)
        sleep(1)

    def player_move(self, coords):
        if not self.field_idx:
            string, column = (coords[1] - 210) // CELL_SIZE, (coords[0] - 510) // CELL_SIZE
        else:
            string, column = (coords[1] - 210) // CELL_SIZE, (coords[0] - 120) // CELL_SIZE
        return self.fields[abs(self.field_idx - 1)].make_move(string, column, coords, self.field_idx)

    def two_players_game_check(self):
        if all([True if i.state == i.ship_len() else False for i in ship_groups[0].sprites()]):
            self.result = 'Игрок 2 выйграл!'
            self.winning_sound.play()
            self.scenes_idx += 1
            sleep(2)
        elif all([True if i.state == i.ship_len() else False for i in ship_groups[1].sprites()]):
            self.result = 'Игрок 1 выйграл!'
            self.defeat_sound.play()
            self.scenes_idx += 1
            sleep(2)

    def robot_game_check(self):
        if all([True if i.state == i.ship_len() else False for i in ship_groups[0].sprites()]):
            self.result = 'Вы проиграли.'
            self.winning_sound.play()
            self.scenes_idx += 1
            sleep(2)
        elif all([True if i.state == i.ship_len() else False for i in ship_groups[1].sprites()]):
            self.result = 'Вы выйграли!'
            self.winning_sound.play()
            self.scenes_idx += 1
            sleep(2)


class GameField:
    def __init__(self):
        self.field = [[None for j in range(10)] for i in range(10)]
        self.shell_sound = pygame.mixer.Sound(load_sound('shell_sound.wav'))
        self.cross_sound = pygame.mixer.Sound(load_sound('cross_sound.wav'))

    def generate_random_field(self, ship_list):
        for i in ship_list[::-1]:
            i.rect.x = SHIFT + 60 + randint(0, 9) * CELL_SIZE
            i.rect.y = SHIFT + 150 + randint(0, 9) * CELL_SIZE
            if choice([True, False]):
                i.rotate()
            while not i.correct_coords(ship_list):
                i.rect.x = SHIFT + 60 + randint(0, 9) * CELL_SIZE
                i.rect.y = SHIFT + 150 + randint(0, 9) * CELL_SIZE
                if choice([True, False]):
                    i.rotate()

    def set_field(self, ship_list):
        for i in ship_list:
            if not i.isrotated():
                for j in range(i.ship_len()):
                    self.field[(i.rect.y - SHIFT - 150) // CELL_SIZE][(i.rect.x - SHIFT - 60) // CELL_SIZE + j] = i
            else:
                for j in range(i.ship_len()):
                    self.field[(i.rect.y - SHIFT - 150) // CELL_SIZE + j][(i.rect.x - SHIFT - 60) // CELL_SIZE] = i

    def make_move(self, i, j, coords, field_idx):
        if self.field[i][j] != 'not available':
            if not self.field[i][j]:
                Shell(shell_group, coords[0] // CELL_SIZE * CELL_SIZE, coords[1] // CELL_SIZE * CELL_SIZE)
                self.shell_sound.play()
                self.field[i][j] = 'not available'
            else:
                Cross(cross_group, coords[0] // CELL_SIZE * CELL_SIZE, coords[1] // CELL_SIZE * CELL_SIZE)
                self.cross_sound.play()

                if self.field[i][j].state < self.field[i][j].ship_len():
                    self.field[i][j].state += 1
                    if self.field[i][j].state == self.field[i][j].ship_len():
                        self.around_the_ship(i, j, field_idx)
                        visible_ships.add(self.field[i][j])
                self.field[i][j] = 'not available'
                return 1
        else:
            return 1

    def around_the_ship(self, i, j, field_idx):
        ship = self.field[i][j]

        if not field_idx:
            xfield = (ship.rect.x - 510) // CELL_SIZE
        else:
            xfield = (ship.rect.x - 120) // CELL_SIZE
        yfield = (ship.rect.y - 210) // CELL_SIZE

        if ship.angle == 90:
            for num_cell in range(-1, ship.ship_len() + 1):
                if self.correct_position(Shell(shell_group, ship.rect.x + CELL_SIZE * num_cell,
                                               ship.rect.y - CELL_SIZE)):
                    self.field[yfield - 1][xfield + num_cell] = 'not available'

                if self.correct_position(Shell(shell_group, ship.rect.x + CELL_SIZE * num_cell,
                                               ship.rect.y + CELL_SIZE)):
                    self.field[yfield + 1][xfield + num_cell] = 'not available'

            if self.correct_position(Shell(shell_group, ship.rect.x + CELL_SIZE * ship.ship_len(),
                                           ship.rect.y)):
                self.field[yfield][xfield + ship.ship_len()] = 'not available'

            if self.correct_position(Shell(shell_group, ship.rect.x - CELL_SIZE, ship.rect.y)):
                self.field[yfield][xfield - 1] = 'not available'
        else:
            for num_cell in range(-1, ship.ship_len() + 1):
                if self.correct_position(Shell(shell_group, ship.rect.x - CELL_SIZE,
                                               ship.rect.y + CELL_SIZE * num_cell)):
                    self.field[yfield + num_cell][xfield - 1] = 'not available'

                if self.correct_position(Shell(shell_group, ship.rect.x + CELL_SIZE,
                                               ship.rect.y + CELL_SIZE * num_cell)):
                    self.field[yfield + num_cell][xfield + 1] = 'not available'

            if self.correct_position(Shell(shell_group, ship.rect.x,
                                           ship.rect.y + CELL_SIZE * ship.ship_len())):
                self.field[yfield + ship.ship_len()][xfield] = 'not available'

            if self.correct_position(Shell(shell_group, ship.rect.x, ship.rect.y - CELL_SIZE)):
                self.field[yfield - 1][xfield] = 'not available'

    def correct_position(self, shell):
        if not pygame.Rect(SHIFT + 2 * CELL_SIZE, SHIFT + 5 * CELL_SIZE,
                           10 * CELL_SIZE, 10 * CELL_SIZE).contains(shell.rect) and \
                not pygame.Rect(SHIFT + 15 * CELL_SIZE, SHIFT + 5 * CELL_SIZE,
                                10 * CELL_SIZE, 10 * CELL_SIZE).contains(shell.rect):
            shell.kill()
            return False
        return True


class Ship(pygame.sprite.Sprite):
    def __init__(self, group, type, x, y):
        super().__init__(group)
        self.type = type
        self.group = group
        self.image = load_image(f"{type}-deck ship.png")
        self.state = 0
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.prev_coords = (x, y)
        self.angle = 90

    def correct_coords(self, list_ships):
        if len([1 for i in list_ships
                if pygame.Rect(self.rect.x - 30, self.rect.y - 30,
                               self.rect.width + 60, self.rect.height + 60).colliderect(i.rect)]) == 1 and \
           pygame.Rect(SHIFT + 60, SHIFT + 150, 300, 300).contains(self.rect):
            return True
        return False

    def rotate(self):
        if self.angle == 90:
            self.image = pygame.transform.flip(
                pygame.transform.rotate(self.image, self.angle), False, True)
        else:
            self.image = pygame.transform.flip(
                pygame.transform.rotate(self.image, self.angle), True, False)
        x, y = self.rect.x, self.rect.y
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.angle = -self.angle

    def ship_len(self):
        if self.type == 'forth':
            return 4
        elif self.type == 'third':
            return 3
        elif self.type == 'double':
            return 2
        return 1

    def isrotated(self):
        if self.angle == 90:
            return False
        return True


class Shell(pygame.sprite.Sprite):
    def __init__(self, group, x, y):
        super().__init__(group)
        self.image = load_image("shell.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Cross(pygame.sprite.Sprite):
    def __init__(self, group, x, y):
        super().__init__(group)
        self.image = load_image("cross.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Background:
    def draw_background(self):
        pygame.draw.rect(SCREEN, 'white', (SHIFT, SHIFT, 810, 480))
        for i in range(0, 810, CELL_SIZE):
            for j in range(0, 480, CELL_SIZE):
                pygame.draw.rect(SCREEN, (135, 206, 235),
                                 (i + SHIFT, j + SHIFT,
                                  CELL_SIZE, CELL_SIZE), 2)
        pygame.draw.line(SCREEN, 'red', (SHIFT, SHIFT + 90),
                         (SHIFT + 810, SHIFT + 90), 3)

    def draw_field(self, coord):
        pygame.draw.rect(SCREEN, 'blue', (SHIFT + coord[0], SHIFT + 150, 300, 300), 3)
        font = pygame.font.Font(None, 30)
        for i in range(1, 11):
            text = font.render(str(i), True, (0, 0, 255))
            if i == 10:
                SCREEN.blit(text, (i * CELL_SIZE + coord[1] - 5,
                                   4 * CELL_SIZE + SHIFT + 5))
            else:
                SCREEN.blit(text, (i * CELL_SIZE + coord[1],
                                   4 * CELL_SIZE + SHIFT + 5))
        string = 'абвгдеёжзи'
        for i in range(10):
            text = font.render(string[i], True, (0, 0, 255))
            if i == 4 or i == 7:
                SCREEN.blit(text, (SHIFT + 5 + coord[2] - 2,
                                   (5 + i) * CELL_SIZE + SHIFT + 5))
            else:
                SCREEN.blit(text, (SHIFT + 5 + coord[2],
                                   (5 + i) * CELL_SIZE + SHIFT + 5))

    def begin_scene(self, num_scene):
        SCREEN.blit(load_image("background.jpg"), (0, 0))
        self.draw_background()
        SCREEN.blit(load_image("menu_picture.png"), (450, 210))
        SCREEN.blit(load_image("pen.png"), (600, -30))

        font = pygame.font.SysFont("Segoe Print", 50)
        if num_scene == 0:
            text = font.render("Играть", True, (0, 0, 255))
            SCREEN.blit(text, (150, 340))
            pygame.draw.rect(SCREEN, (0, 0, 255), (140, 350, 230, 80), 5)
        else:
            text = font.render("Робот", True, (0, 0, 255))
            SCREEN.blit(text, (180, 290))
            pygame.draw.rect(SCREEN, (0, 0, 255), (140, 300, 250, 80), 5)

            text = font.render("2 игрока", True, (0, 0, 255))
            SCREEN.blit(text, (150, 390))
            pygame.draw.rect(SCREEN, (0, 0, 255), (140, 400, 250, 80), 5)

        font.set_bold(True)
        text = font.render("Морской бой", True, (0, 0, 255))
        SCREEN.blit(text, (80, 180))

    def placement_of_ships_scene(self):
        SCREEN.blit(load_image("background.jpg"), (0, 0))
        self.draw_background()
        self.draw_field((60, 100, 35))

        font = pygame.font.SysFont("Segoe Print", 30)
        text = font.render("Далее", True, (0, 0, 255))
        SCREEN.blit(text, (720, 465))
        pygame.draw.rect(SCREEN, (0, 0, 255), (710, 470, 115, 50), 5)

        text = font.render("Авто", True, (0, 0, 255))
        SCREEN.blit(text, (570, 465))
        pygame.draw.rect(SCREEN, (0, 0, 255), (560, 470, 110, 50), 5)

        SCREEN.blit(load_image("reset.png"), (450, 450))
        pygame.draw.rect(SCREEN, (0, 0, 255), (440, 440, 80, 80), 5)

        pygame.draw.polygon(SCREEN, (0, 0, 255), ((120, 90), (90, 105), (120, 120)))
        pygame.draw.rect(SCREEN, (0, 0, 255), (120, 100, 30, 10))
        pygame.draw.rect(SCREEN, (0, 0, 255), (80, 80, 80, 50), 5)

    def battle_scene(self, mode, field_idx):
        SCREEN.blit(load_image("background.jpg"), (0, 0))
        self.draw_background()
        self.draw_field((60, 100, 35))
        self.draw_field((450, 490, 755))

        pygame.draw.polygon(SCREEN, (0, 0, 255), ((120, 90), (90, 105), (120, 120)))
        pygame.draw.rect(SCREEN, (0, 0, 255), (120, 100, 30, 10))
        pygame.draw.rect(SCREEN, (0, 0, 255), (80, 80, 80, 50), 5)

        font = pygame.font.SysFont("Segoe Print", 30)
        if mode == 'Робот':
            text = font.render("Игрок", True, (0, 0, 255))
            SCREEN.blit(text, (220, 80))
            text = font.render("Робот", True, (0, 0, 255))
            SCREEN.blit(text, (610, 80))
        else:
            text = font.render("Игрок 1", True, (0, 0, 255))
            SCREEN.blit(text, (205, 80))
            text = font.render("Игрок 2", True, (0, 0, 255))
            SCREEN.blit(text, (595, 80))

        if not field_idx:
            pygame.draw.polygon(SCREEN, (0, 180, 0), ((465, 345), (495, 360), (465, 375)))
            pygame.draw.rect(SCREEN, (0, 180, 0), (435, 355, 30, 10))
        else:
            pygame.draw.polygon(SCREEN, (0, 180, 0), ((465, 345), (435, 360), (465, 375)))
            pygame.draw.rect(SCREEN, (0, 180, 0), (465, 355, 30, 10))

    def result_scene(self, text):
        SCREEN.blit(load_image("background.jpg"), (0, 0))
        self.draw_background()
        if text == 'Вы проиграли!':
            SCREEN.blit(load_image("defeat.png"), (480, 150))
        else:
            SCREEN.blit(load_image("winning.png"), (480, 210))

        font = pygame.font.SysFont("Segoe Print", 35)
        font.set_bold(True)
        text = font.render(text, True, (0, 0, 255))
        SCREEN.blit(text, (90, 195))

        font = pygame.font.SysFont("Segoe Print", 30)
        text = font.render('Кликните, чтобы', True, (0, 0, 255))
        SCREEN.blit(text, (90, 290))
        text = font.render('продолжить.', True, (0, 0, 255))
        SCREEN.blit(text, (120, 350))


def main():
    if __name__ == '__main__':
        game = Game()
        game.game_loop()
        pygame.quit()


main()
