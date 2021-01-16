import pygame
import os
import sys
from random import randint, choice

pygame.init()

# константы
SIZE = 1020, 690
SCREEN = pygame.display.set_mode(SIZE)
SHIFT = 60
CELL_SIZE = 30
FPS = 10

# группы спрайтов
ship_groups = [pygame.sprite.Group(), pygame.sprite.Group()]
shell_group = pygame.sprite.Group()
cross_group = pygame.sprite.Group()
fire_group = pygame.sprite.Group()
visible_ships = pygame.sprite.Group()


def load_image(name, colorkey=None):
    # загрузка изображения
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
    # проверка на существование музыки
    fullname = os.path.join('data', 'music', name)
    if not os.path.isfile(fullname):
        print(f"Файл с музыкой '{fullname}' не найден")
        sys.exit()
    return fullname


class Game:
    def __init__(self):
        pygame.display.set_caption('Морской бой')

        self.background = Background()

        # номер сцены
        self.scenes_idx = 0

        # переменная для переноса кораблей
        self.selected_ship = None
        # переменная для поворота корабля и его перестановки на предыдущее место
        # в случае неверных координат
        self.last_selected_ship = None

        # два поля и переменная, которая отвечает за то, кто ходит
        self.fields = [GameField(), GameField()]
        self.field_idx = 0

        # флаги для отрисовки групп кораблей двух игроков
        self.flag_ship_group1 = False
        self.flag_ship_group2 = False

        # загрузка музыки для окончания игры
        self.winning_sound = pygame.mixer.Sound(load_sound('winning.wav'))
        self.defeat_sound = pygame.mixer.Sound(load_sound('defeat.wav'))
        # проверка наличия текстового файла
        if not os.path.isfile('data/statistic.txt'):
            print(f"Текстовый файл 'statistic.txt' не найден")
            sys.exit()

        # флаг используется для реализации задержки хода робота
        self.robot_flag = None
        # флаг используется для реализации задержки после последнего хода
        self.game_over_flag = None

        self.letter_keys = [pygame.K_f, pygame.K_COMMA, pygame.K_d, pygame.K_u, pygame.K_l,
                            pygame.K_t, pygame.K_BACKQUOTE, pygame.K_SEMICOLON, pygame.K_p, pygame.K_b]
        self.number_keys = [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                            pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]

    def game_loop(self):
        # фоновая музыка
        pygame.mixer.music.load(load_sound('soundtrack.wav'))
        pygame.mixer.music.set_volume(0.03)
        pygame.mixer.music.play(loops=-1)

        clock = pygame.time.Clock()

        running = True
        while running:
            mods = pygame.key.get_mods()
            for event in pygame.event.get():
                # выход
                if event.type == pygame.QUIT:
                    running = False

                # кнопка "Играть"
                elif self.scenes_idx == 0 and event.type == pygame.MOUSEBUTTONDOWN and \
                        (self.isbtn(event.pos[0], 140, 370) and self.isbtn(event.pos[1], 380, 460)):
                    # новая сцена
                    self.scenes_idx += 1

                # выбор режима: "Робот" или "2 игрока"
                elif self.scenes_idx == 1 and event.type == pygame.MOUSEBUTTONDOWN and \
                        self.isbtn(event.pos[0], 140, 390) and \
                        (self.isbtn(event.pos[1], 330, 410) or self.isbtn(event.pos[1], 430, 510)):
                    self.set_mode(event)

                # кнопка "Назад"
                elif (self.scenes_idx in [2, 3] and mods & pygame.KMOD_CTRL and
                      event.type == pygame.KEYDOWN and event.key == pygame.K_b) or \
                        (event.type == pygame.MOUSEBUTTONDOWN and
                         (self.scenes_idx == 4 or
                          (self.scenes_idx in [2, 3] and self.isbtn(event.pos[0], 80, 160) and
                           self.isbtn(event.pos[1], 80, 130)))):
                    self.back()

                # кнопка "поворот"
                elif self.scenes_idx == 2 and self.last_selected_ship and \
                        ((mods & pygame.KMOD_CTRL and event.type == pygame.KEYDOWN and event.key == pygame.K_r) or
                         (event.type == pygame.MOUSEBUTTONDOWN and self.isbtn(event.pos[0], 500, 580) and
                          self.isbtn(event.pos[1], 500, 580))) and \
                        self.last_selected_ship.type != 'single':
                    # поворачиваем
                    self.last_selected_ship.rotate()
                    # позиция корабля не соответствует правилам игры - возращаем обратно
                    if not self.last_selected_ship.correct_coords(ship_groups[self.field_idx].sprites()):
                        self.last_selected_ship.rotate()

                # кнопка "Авто"
                elif self.scenes_idx == 2 and \
                        ((mods & pygame.KMOD_CTRL and event.type == pygame.KEYDOWN and event.key == pygame.K_a) or
                         (event.type == pygame.MOUSEBUTTONDOWN and self.isbtn(event.pos[0], 620, 730) and
                          self.isbtn(event.pos[1], 530, 580))):
                    # генерируем случайную расстановку кораблей
                    self.fields[self.field_idx].generate_random_field(ship_groups[self.field_idx].sprites())

                # кнопка "Далее"
                elif self.scenes_idx == 2 and \
                        ((mods & pygame.KMOD_CTRL and event.type == pygame.KEYDOWN and event.key == pygame.K_n) or
                         (event.type == pygame.MOUSEBUTTONDOWN and self.isbtn(event.pos[0], 770, 885) and
                          self.isbtn(event.pos[1], 530, 580))) and \
                        not [1 for i in ship_groups[self.field_idx].sprites()
                             if not pygame.Rect(SHIFT + 90, SHIFT + 180, 300, 300).contains(i.rect)]:
                    self.preparation_for_battle()

                # взятие корабля
                elif self.scenes_idx == 2 and event.type == pygame.MOUSEBUTTONDOWN:
                    result = [i for i in ship_groups[self.field_idx].sprites()
                              if i.rect.collidepoint(*event.pos)]
                    # если мышка кликнула на один из кораблей
                    if result:
                        # фиксируем это в переменной
                        self.selected_ship = result[0]
                        self.move_coords = event.pos

                # перемещение корабля
                elif self.scenes_idx == 2 and event.type == pygame.MOUSEMOTION and self.selected_ship:
                    self.selected_ship.rect.x += event.pos[0] - self.move_coords[0]
                    self.selected_ship.rect.y += event.pos[1] - self.move_coords[1]
                    self.move_coords = event.pos

                # отпускание корабля
                elif self.scenes_idx == 2 and event.type == pygame.MOUSEBUTTONUP and self.selected_ship:
                    self.put_ship()

                # обработка хода для двух людей
                elif self.scenes_idx == 3 and event.type == pygame.MOUSEBUTTONDOWN and self.mode == '2 игрока' and \
                        ((not self.field_idx and self.isbtn(event.pos[0], 570, 870)) or
                         (self.field_idx and self.isbtn(event.pos[0], 180, 480))) and\
                        self.isbtn(event.pos[1], 240, 540):
                    if not self.game_over_flag and not self.player_move(event.pos):
                        # если один игрок промахнулся - ход сдедующего
                        self.field_idx = abs(self.field_idx - 1)
                    # кончилась ли игра
                    self.two_players_game_check()

                elif self.scenes_idx == 3 and event.type == pygame.MOUSEBUTTONDOWN and self.mode == 'Робот' and \
                        self.isbtn(event.pos[0], 570, 870) and self.isbtn(event.pos[1], 240, 540):
                    # если игрок промахнулся
                    if not self.robot_flag and not self.game_over_flag and not self.player_move(event.pos):
                        # меняем ход
                        self.field_idx = abs(self.field_idx - 1)
                        # флаг для задержки
                        self.robot_flag = True
                    else:
                        # кончилась ли игра
                        self.robot_game_check()

                # ход с помощью клавиатуры
                elif self.scenes_idx == 3 and \
                        [i for i in pygame.key.get_pressed() if i in self.letter_keys] and \
                        [i for i in pygame.key.get_pressed() if i in self.number_keys]:
                    pass

            # реализация задержки
            time_idx = 0
            while (time_idx < 10 and self.robot_flag) or (self.game_over_flag and time_idx < 20) or \
                    (time_idx == 0 and not self.robot_flag):
                self.drawing_sprites()

                pygame.display.flip()
                clock.tick(FPS)
                time_idx += 1

            self.frezzing()

    def drawing_sprites(self):
        SCREEN.fill(0)

        # отрисовка сцены
        if self.scenes_idx < 2:
            self.background.begin_scene(self.scenes_idx)
        elif self.scenes_idx == 2:
            self.background.placement_of_ships_scene()
            if self.last_selected_ship:
                pygame.draw.rect(SCREEN, (255, 0, 0), self.last_selected_ship.rect, 3)
        elif self.scenes_idx == 3:
            self.background.battle_scene(self.mode, self.field_idx,
                                         [self.fields[0].shoot_count, self.fields[1].shoot_count],
                                         [self.fields[0].ships_count, self.fields[1].ships_count])
            # отрисовка спрайтов кораблей в бою, снарядов, крестиков
            visible_ships.draw(SCREEN)
            shell_group.draw(SCREEN)
            shell_group.update()
            fire_group.draw(SCREEN)
            fire_group.update()
            cross_group.draw(SCREEN)
        elif self.scenes_idx == 4:
            self.background.result_scene(self.mode, self.result)

        # отрисовка спрайтов кораблей при расстановки
        if self.flag_ship_group1:
            ship_groups[0].draw(SCREEN)
        if self.flag_ship_group2:
            ship_groups[1].draw(SCREEN)

    def isbtn(self, pos, min_pos, max_pos):
        if min_pos <= pos < max_pos:
            return True
        return False

    def init_ships(self, group):
        # иницилизация кораблей
        for i in [['single', 540, 240], ['single', 600, 240], ['single', 660, 240], ['single', 720, 240],
                  ['double', 540, 300], ['double', 630, 300], ['double', 720, 300], ['third', 540, 360],
                  ['third', 660, 360], ['forth', 540, 420]]:
            Ship(group, *i)

    def change_statistic(self, text):
        # изменение статистики
        with open('data/statistic.txt', 'r') as file:
            str_file = file.read()

        score = [[int(j) for j in i.split(', ')] for i in str_file.split('; ')]
        if text == 'Вы проиграли.':
            score[0][1] += 1
        elif self.mode == 'Робот':
            score[0][0] += 1
        elif '1' in text:
            score[1][0] += 1
        else:
            score[1][1] += 1

        with open('data/statistic.txt', 'w', encoding='utf-8') as file:
            file.write('; '.join(', '.join(str(j) for j in i) for i in score))

    def frezzing(self):
        if self.robot_flag:
            # ход робота
            if self.robot_move():
                # в случае попадания по кораблю даётся ещё одна попытка
                # проверяем кончилась ли игра с роботом
                self.robot_game_check()
            else:
                # иначе ход даётся игроку
                self.field_idx = abs(self.field_idx - 1)
                # заперщаем роботу ходить
                self.robot_flag = None
        elif self.game_over_flag:
            # новая сцена
            self.scenes_idx += 1
            self.game_over_flag = None
            self.change_statistic(self.result)

    def put_ship(self):
        # ставим корабль точно в клетки
        self.selected_ship.rect.x = round(self.selected_ship.rect.x / CELL_SIZE) * CELL_SIZE
        self.selected_ship.rect.y = round(self.selected_ship.rect.y / CELL_SIZE) * CELL_SIZE
        if self.selected_ship.correct_coords(ship_groups[self.field_idx].sprites()):
            # если координаты корабля верные, сохраняем их
            self.selected_ship.prev_coords = self.selected_ship.rect.x, self.selected_ship.rect.y
        else:
            # если нет, меняем на предыдущие
            self.selected_ship.rect.x = self.selected_ship.prev_coords[0]
            self.selected_ship.rect.y = self.selected_ship.prev_coords[1]
        self.last_selected_ship = self.selected_ship
        # корабль больше не следует за стрелкой миши
        self.selected_ship = None

    def preparation_for_battle(self):
        # для робота генерируем случайную расстановку кораблей
        if self.mode == 'Робот':
            self.fields[self.field_idx].generate_random_field(ship_groups[self.field_idx + 1].sprites())

        if self.mode == 'Робот' or self.field_idx == 1:
            # если это последняя сцена перед боем
            for i in range(len(self.fields)):
                # расставляем экземпляры класса корабль в двумерный список
                self.fields[i].set_field(ship_groups[i].sprites())
            for i in ship_groups[0].sprites():
                # корабли левого игрока двигаем
                i.rect.x += 30
            for i in ship_groups[1].sprites():
                # корабли правого игрока двигаем
                i.rect.x += 420

            self.flag_ship_group1 = self.flag_ship_group2 = False
            if self.mode == 'Робот':
                # добавляем в группу видимых спрайтов корабли игрока
                # если режим игры робот
                visible_ships.add(*ship_groups[0].sprites())

            self.field_idx = -1
            # новая сцена
            self.scenes_idx += 1
        else:
            # если это не последняя сцена перед боем
            # рисуем корабли второй группы
            self.flag_ship_group1 = False
            self.flag_ship_group2 = True
        # следующее поле
        self.field_idx += 1

    def back(self):
        # возращаемся в меню
        self.scenes_idx = 1
        # ход первому игроку
        self.field_idx = 0
        # новые поля
        self.fields = [GameField(), GameField()]
        # очищаем группы
        for i in ship_groups:
            i.empty()
        shell_group.empty()
        cross_group.empty()
        fire_group.empty()
        visible_ships.empty()
        # запрещаем показывать корабли
        self.flag_ship_group1 = False
        self.flag_ship_group2 = False

        self.last_selected_ship = None
        self.selected_ship = None

    def set_mode(self, event):
        # определяем режим
        if self.isbtn(event.pos[1], 330, 410):
            self.mode = 'Робот'
        else:
            self.mode = '2 игрока'
        # новая сцена
        self.scenes_idx += 1
        # иницилизация кораблей
        self.init_ships(ship_groups[0])
        self.init_ships(ship_groups[1])
        #  показываем первую группу
        self.flag_ship_group1 = True

    def robot_move(self):
        # случайный ход
        i, j = randint(0, 9), randint(0, 9)
        # главное, чтобы до этого он не ходил ещё в неё
        while self.fields[0].field[i][j] == 'not available':
            i, j = randint(0, 9), randint(0, 9)
        # делаем ход
        return self.fields[0].make_move(i, j, (j * CELL_SIZE + 180, i * CELL_SIZE + 240), self.field_idx)

    def player_move(self, coords):
        # определяем координаты в матрице
        if not self.field_idx:
            string, column = (coords[1] - 240) // CELL_SIZE, (coords[0] - 570) // CELL_SIZE
        else:
            string, column = (coords[1] - 240) // CELL_SIZE, (coords[0] - 180) // CELL_SIZE
        # делаем ход
        return self.fields[abs(self.field_idx - 1)].make_move(string, column, coords, self.field_idx)

    def two_players_game_check(self):
        # если количество снесённых мачт совпадает с количеством  мачт
        if all([True if i.state == i.ship_len() else False for i in ship_groups[0].sprites()]):
            self.result = 'Игрок 2 выиграл!'
            self.winning_sound.play()
            # делаем задержку
            self.game_over_flag = True
        elif all([True if i.state == i.ship_len() else False for i in ship_groups[1].sprites()]):
            self.result = 'Игрок 1 выиграл!'
            self.winning_sound.play()
            # делаем задержку
            self.game_over_flag = True

        if self.game_over_flag:
            visible_ships.empty()
            for i in ship_groups:
                visible_ships.add(*i)

    def robot_game_check(self):
        # если количество снесённых мачт совпадает с количеством  мачт
        if all([True if i.state == i.ship_len() else False for i in ship_groups[0].sprites()]):
            self.result = 'Вы проиграли.'
            self.defeat_sound.play()
            # делаем задержку
            self.game_over_flag = True
        elif all([True if i.state == i.ship_len() else False for i in ship_groups[1].sprites()]):
            self.result = 'Вы выиграли!'
            self.winning_sound.play()
            # делаем задержку
            self.game_over_flag = True

        if self.game_over_flag:
            visible_ships.empty()
            for i in ship_groups:
                visible_ships.add(*i)


class GameField:
    def __init__(self):
        self.field = [[None for j in range(10)] for i in range(10)]
        # звук снаряда
        self.shell_sound = pygame.mixer.Sound(load_sound('shell_sound.wav'))
        # звук попадания а корабль
        self.cross_sound = pygame.mixer.Sound(load_sound('cross_sound.wav'))
        # количество выстрелов
        self.shoot_count = 0
        # количество оставшихся кораблей
        self.ships_count = 10

    def generate_random_field(self, ship_list):
        # идём от самого большого к самому маленькому
        for i in ship_list[::-1]:
            i.rect.x = SHIFT + 90 + randint(0, 9) * CELL_SIZE
            i.rect.y = SHIFT + 180 + randint(0, 9) * CELL_SIZE
            i.prev_coords = i.rect.x, i.rect.y
            # повёрнут или нет (однопалубные корабли не поворачиваем)
            if choice([True, False]) and i.ship_len() > 1:
                i.rotate()
            # если координаты не верны, генерируем новые
            while not i.correct_coords(ship_list):
                i.rect.x = SHIFT + 90 + randint(0, 9) * CELL_SIZE
                i.rect.y = SHIFT + 180 + randint(0, 9) * CELL_SIZE
                i.prev_coords = i.rect.x, i.rect.y
                # повёрнут или нет
                if choice([True, False]) and i.ship_len() > 1:
                    i.rotate()

    def set_field(self, ship_list):
        # помещаем экземпляры класса корабль в матрицу
        for i in ship_list:
            # корабль повёрнут
            if not i.isrotated():
                # помещаем экземпляр корабля в каждую клеточку, которую он занимает
                for j in range(i.ship_len()):
                    self.field[(i.rect.y - SHIFT - 180) // CELL_SIZE][(i.rect.x - SHIFT - 90) // CELL_SIZE + j] = i
            else:
                for j in range(i.ship_len()):
                    self.field[(i.rect.y - SHIFT - 180) // CELL_SIZE + j][(i.rect.x - SHIFT - 90) // CELL_SIZE] = i

    def make_move(self, i, j, coords, field_idx):
        # делаем ход
        # если в клетку ещё не был сделан ход
        if self.field[i][j] != 'not available':
            # увеличиваем количество выстрелов
            self.shoot_count += 1
            if not self.field[i][j]:
                # если промахнулся
                Shell(3, 2, coords[0] // CELL_SIZE * CELL_SIZE, coords[1] // CELL_SIZE * CELL_SIZE)
                self.shell_sound.play()
                # запрещаем сюда ходить
                self.field[i][j] = 'not available'
            else:
                # если попал
                Fire(8, 4, coords[0] // CELL_SIZE * CELL_SIZE, coords[1] // CELL_SIZE * CELL_SIZE)
                self.cross_sound.play()

                # прибавляем к количеству снесённых мачт
                self.field[i][j].state += 1
                # если корабль полностью побит
                if self.field[i][j].state == self.field[i][j].ship_len():
                    # окружаем его снарядами
                    self.around_the_ship(i, j, field_idx)
                    # показываем корабль
                    visible_ships.add(self.field[i][j])
                    # уменьшаем количество оставшихся кораблей
                    self.ships_count -= 1
                # запрещаем сюда ходить
                self.field[i][j] = 'not available'

                return 1
        else:
            return 1

    def around_the_ship(self, i, j, field_idx):
        # окружаем корабль снарядами
        ship = self.field[i][j]

        if not field_idx:
            # ход на левое поле
            jfield = (ship.rect.x - 570) // CELL_SIZE
        else:
            # ход на правое поле
            jfield = (ship.rect.x - 180) // CELL_SIZE
        # индекс строки матрицы для обоих полей одинаков
        ifield = (ship.rect.y - 240) // CELL_SIZE

        if not ship.isrotated():
            # если корабль не повёрнут (горизонтальное положение)
            for num_cell in range(-1, ship.ship_len() + 1):
                # окружаем снарядами корабль снизу и сверху

                # если снаряд не вышел за края полей не трогаем его
                if self.correct_position(Cross(ship.rect.x + CELL_SIZE * num_cell,
                                               ship.rect.y - CELL_SIZE)):
                    # запрещаем туда ходить
                    self.field[ifield - 1][jfield + num_cell] = 'not available'

                if self.correct_position(Cross(ship.rect.x + CELL_SIZE * num_cell,
                                               ship.rect.y + CELL_SIZE)):
                    self.field[ifield + 1][jfield + num_cell] = 'not available'

            # а затем по одному снаряду с боков
            if self.correct_position(Cross(ship.rect.x + CELL_SIZE * ship.ship_len(),
                                           ship.rect.y)):
                self.field[ifield][jfield + ship.ship_len()] = 'not available'

            if self.correct_position(Cross(ship.rect.x - CELL_SIZE, ship.rect.y)):
                self.field[ifield][jfield - 1] = 'not available'
        else:
            # если корабль повёрнут (вертикальное положение)
            for num_cell in range(-1, ship.ship_len() + 1):
                # окружаем снарядами корабль справа и слева
                if self.correct_position(Cross(ship.rect.x - CELL_SIZE,
                                               ship.rect.y + CELL_SIZE * num_cell)):
                    self.field[ifield + num_cell][jfield - 1] = 'not available'

                if self.correct_position(Cross(ship.rect.x + CELL_SIZE,
                                               ship.rect.y + CELL_SIZE * num_cell)):
                    self.field[ifield + num_cell][jfield + 1] = 'not available'

            # а затем по одному снаряду сверху и снизу
            if self.correct_position(Cross(ship.rect.x,
                                           ship.rect.y + CELL_SIZE * ship.ship_len())):
                self.field[ifield + ship.ship_len()][jfield] = 'not available'

            if self.correct_position(Cross(ship.rect.x, ship.rect.y - CELL_SIZE)):
                self.field[ifield - 1][jfield] = 'not available'

    def correct_position(self, shell):
        # если снаряд вышел за края полей
        if not pygame.Rect(SHIFT + 4 * CELL_SIZE, SHIFT + 6 * CELL_SIZE,
                           10 * CELL_SIZE, 10 * CELL_SIZE).contains(shell.rect) and \
                not pygame.Rect(SHIFT + 17 * CELL_SIZE, SHIFT + 6 * CELL_SIZE,
                                10 * CELL_SIZE, 10 * CELL_SIZE).contains(shell.rect):
            # убиваем спрайт
            shell.kill()
            return False
        return True


class Ship(pygame.sprite.Sprite):
    def __init__(self, group, type, x, y):
        super().__init__(group)
        # тип корабля
        self.type = type
        # загружаем его изображение
        self.image = load_image(f"{type}-deck ship.png")
        # количество попаданий
        self.state = 0

        # координаты
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # предыдущие координаты
        self.prev_coords = (x, y)
        # угол поворота
        self.angle = 90

    def correct_coords(self, list_ships):
        # проверка на правильные координаты корабля
        # если он не пересекается с другими кораблями
        # и не выходит за границы поля
        # значит возращаем True
        if len([1 for i in list_ships
                if pygame.Rect(self.rect.x - 30, self.rect.y - 30,
                               self.rect.width + 60, self.rect.height + 60).colliderect(i.rect)]) == 1 and \
           pygame.Rect(SHIFT + 90, SHIFT + 180, 300, 300).contains(self.rect):
            return True
        return False

    def rotate(self):
        # если корабль находится в горизонтальном положении
        if self.angle == 90:
            # крутим на 90 градусов по часовой стрелке
            self.image = pygame.transform.flip(
                pygame.transform.rotate(self.image, self.angle), False, True)
        else:
            # крутим на 90 градусов против часовой стрелке
            self.image = pygame.transform.flip(
                pygame.transform.rotate(self.image, self.angle), True, False)
        # запоминаем координаты
        x, y = self.rect.x, self.rect.y
        # получаем прямоугольник
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        # меняем угол поворота
        self.angle = -self.angle

    def ship_len(self):
        # длинв корабля
        if self.type == 'forth':
            return 4
        elif self.type == 'third':
            return 3
        elif self.type == 'double':
            return 2
        return 1

    def isrotated(self):
        # повёрнут ли корабль
        if self.angle == 90:
            return False
        return True


# снаряд
class Shell(pygame.sprite.Sprite):
    def __init__(self, columns, rows, x, y):
        super().__init__(shell_group)
        self.image = load_image("shells.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.frames = []
        self.cut_sheet(self.image, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, self.image.get_width() // columns,
                                self.image.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


# огонь
class Fire(pygame.sprite.Sprite):
    def __init__(self, columns, rows, x, y):
        super().__init__(fire_group)
        self.image = load_image("fire.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.frames = []
        self.cut_sheet(self.image, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, self.image.get_width() // columns,
                                self.image.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


# крестик
class Cross(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(cross_group)
        self.image = load_image("cross.png")
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


# задний фон и сцены
class Background:
    def draw_background(self):
        # тетрадный лист
        pygame.draw.rect(SCREEN, 'white', (SHIFT, SHIFT, 900, 570))
        for i in range(0, 900, CELL_SIZE):
            for j in range(0, 570, CELL_SIZE):
                pygame.draw.rect(SCREEN, (135, 206, 235),
                                 (i + SHIFT, j + SHIFT,
                                  CELL_SIZE, CELL_SIZE), 2)
        pygame.draw.line(SCREEN, 'red', (SHIFT, SHIFT + 120),
                         (SHIFT + 900, SHIFT + 120), 3)

    def draw_field(self, coord):
        # рисует поле боя
        pygame.draw.rect(SCREEN, 'blue', (SHIFT + coord[0], SHIFT + 180, 300, 300), 3)
        # цифры
        font = pygame.font.Font(None, 30)
        for i in range(1, 11):
            text = font.render(str(i), True, (0, 0, 255))
            if i == 10:
                SCREEN.blit(text, (i * CELL_SIZE + coord[1] - 5,
                                   5 * CELL_SIZE + SHIFT + 5))
            else:
                SCREEN.blit(text, (i * CELL_SIZE + coord[1],
                                   5 * CELL_SIZE + SHIFT + 5))
        # буквы
        string = 'абвгдеёжзи'
        for i in range(10):
            text = font.render(string[i], True, (0, 0, 255))
            if i == 4 or i == 7:
                SCREEN.blit(text, (SHIFT + 5 + coord[2] - 2,
                                   (6 + i) * CELL_SIZE + SHIFT + 5))
            else:
                SCREEN.blit(text, (SHIFT + 5 + coord[2],
                                   (6 + i) * CELL_SIZE + SHIFT + 5))

    def begin_scene(self, num_scene):
        # меню игры

        # стол
        SCREEN.blit(load_image("background.jpg"), (0, 0))
        # тетрадный лист
        self.draw_background()
        # корабль
        SCREEN.blit(load_image("menu_picture.png"), (510, 240))
        SCREEN.blit(load_image("pen.png"), (660, 0))

        font = pygame.font.SysFont("Segoe Print", 50)
        if num_scene == 0:
            # кнопка "Играть"
            text = font.render("Играть", True, (0, 0, 255))
            SCREEN.blit(text, (150, 370))
            pygame.draw.rect(SCREEN, (0, 0, 255), (140, 380, 230, 80), 5)
        else:
            # кнопка "Робот"
            text = font.render("Робот", True, (0, 0, 255))
            SCREEN.blit(text, (180, 320))
            pygame.draw.rect(SCREEN, (0, 0, 255), (140, 330, 250, 80), 5)
            # кнопка "2 игрока"
            text = font.render("2 игрока", True, (0, 0, 255))
            SCREEN.blit(text, (150, 420))
            pygame.draw.rect(SCREEN, (0, 0, 255), (140, 430, 250, 80), 5)

        # название игры
        font.set_bold(True)
        text = font.render("Морской бой", True, (0, 0, 255))
        SCREEN.blit(text, (80, 210))

    def placement_of_ships_scene(self):
        # стол
        SCREEN.blit(load_image("background.jpg"), (0, 0))
        # тетрадный лист
        self.draw_background()
        # левое поле
        self.draw_field((90, 130, 65))

        # кнопка "Далее"
        font = pygame.font.SysFont("Segoe Print", 30)
        text = font.render("Далее", True, (0, 0, 255))
        SCREEN.blit(text, (780, 525))
        pygame.draw.rect(SCREEN, (0, 0, 255), (770, 530, 115, 50), 5)

        # кнопка "Авто"
        text = font.render("Авто", True, (0, 0, 255))
        SCREEN.blit(text, (630, 525))
        pygame.draw.rect(SCREEN, (0, 0, 255), (620, 530, 110, 50), 5)

        # кнопка "Поворот"
        SCREEN.blit(load_image("reset.png"), (510, 510))
        pygame.draw.rect(SCREEN, (0, 0, 255), (500, 500, 80, 80), 5)

        # кнопка "Назад"
        pygame.draw.polygon(SCREEN, (0, 0, 255), ((120, 90), (90, 105), (120, 120)))
        pygame.draw.rect(SCREEN, (0, 0, 255), (120, 100, 30, 10))
        pygame.draw.rect(SCREEN, (0, 0, 255), (80, 80, 80, 50), 5)

    def battle_scene(self, mode, field_idx, shoot_counts, ships_counts):
        # стол
        SCREEN.blit(load_image("background.jpg"), (0, 0))
        # тетрадный лист
        self.draw_background()
        # боевые поля
        self.draw_field((120, 160, 95))
        self.draw_field((510, 550, 815))

        # кнопка "Назад"
        pygame.draw.polygon(SCREEN, (0, 0, 255), ((120, 90), (90, 105), (120, 120)))
        pygame.draw.rect(SCREEN, (0, 0, 255), (120, 100, 30, 10))
        pygame.draw.rect(SCREEN, (0, 0, 255), (80, 80, 80, 50), 5)

        # Подписи кому пренадлежит данное поле
        font = pygame.font.SysFont("Segoe Print", 35)
        if mode == 'Робот':
            text = font.render("Игрок", True, (0, 0, 255))
            SCREEN.blit(text, (275, 551))
            text = font.render("Робот", True, (0, 0, 255))
            SCREEN.blit(text, (660, 555))
        else:
            text = font.render("Игрок 1", True, (0, 0, 255))
            SCREEN.blit(text, (240, 551))
            text = font.render("Игрок 2", True, (0, 0, 255))
            SCREEN.blit(text, (660, 551))

        font = pygame.font.SysFont("Segoe Print", 24)
        text = font.render(f"Кораблей осталось: {ships_counts[0]}", True, (0, 0, 255))
        SCREEN.blit(text, (180, 85))
        text = font.render(f"Всего выстрелов: {shoot_counts[0]}", True, (0, 0, 255))
        SCREEN.blit(text, (180, 141))
        text = font.render(f"Кораблей осталось: {ships_counts[1]}", True, (0, 0, 255))
        SCREEN.blit(text, (570, 85))
        text = font.render(f"Всего выстрелов: {shoot_counts[1]}", True, (0, 0, 255))
        SCREEN.blit(text, (570, 141))

        # смена напраления стрелки, показывающей чей сейчас ход
        if not field_idx:
            pygame.draw.polygon(SCREEN, (0, 180, 0), ((525, 375), (555, 390), (525, 405)))
            pygame.draw.rect(SCREEN, (0, 180, 0), (495, 385, 30, 10))
        else:
            pygame.draw.polygon(SCREEN, (0, 180, 0), ((525, 375), (495, 390), (525, 405)))
            pygame.draw.rect(SCREEN, (0, 180, 0), (525, 385, 30, 10))

    def result_scene(self, mode, text):
        # результаты игры
        SCREEN.blit(load_image("background.jpg"), (0, 0))
        # тетрадный лист
        self.draw_background()

        with open('data/statistic.txt', 'r') as file:
            str_file = file.read()
        score = [[int(j) for j in i.split(', ')] for i in str_file.split('; ')]

        # фоновое изображение
        if text == 'Вы проиграли!':
            SCREEN.blit(load_image("defeat.png"), (570, 210))
        else:
            SCREEN.blit(load_image("winning.png"), (570, 270))

        # результат
        font = pygame.font.SysFont("Segoe Print", 35)
        font.set_bold(True)
        text = font.render(text, True, (0, 0, 255))
        SCREEN.blit(text, (120, 255))

        # подсказка
        font = pygame.font.SysFont("Segoe Print", 30)
        text = font.render('Кликните, чтобы', True, (0, 0, 255))
        SCREEN.blit(text, (150, 350))
        text = font.render('продолжить.', True, (0, 0, 255))
        SCREEN.blit(text, (180, 410))

        if mode == 'Робот':
            text = font.render(f'Игрок: {score[0][0]}', True, (0, 0, 255))
            SCREEN.blit(text, (90, 90))
            text = font.render(f'Робот: {score[0][1]}', True, (0, 0, 255))
            SCREEN.blit(text, (420, 90))
        else:
            text = font.render(f'Игрок 1: {score[1][0]}', True, (0, 0, 255))
            SCREEN.blit(text, (90, 90))
            text = font.render(f'Игрок 2: {score[1][1]}', True, (0, 0, 255))
            SCREEN.blit(text, (420, 90))


def main():
    if __name__ == '__main__':
        # начало игры
        game = Game()
        game.game_loop()
        pygame.quit()


main()
