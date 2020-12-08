import pygame


class Game:
    def __init__(self):
        self.size = self.width, self.height = 840, 570
        self.screen = pygame.display.set_mode(self.size)
        self.shift = 60
        self.clock = pygame.time.Clock()
        self.cell_size = 30
        self.draw_background()
        self.draw_fields()
        self.game_loop()

    def game_loop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            pygame.display.flip()

    def draw_background(self):
        self.screen.fill((205, 133, 63))
        pygame.draw.rect(self.screen, 'white', (self.shift, self.shift, 720, 450))
        for i in range(0, 720, self.cell_size):
            for j in range(0, 450, self.cell_size):
                pygame.draw.rect(self.screen, (135, 206, 235),
                                 (i + self.shift, j + self.shift,
                                  self.cell_size, self.cell_size), 2)
        pygame.draw.line(self.screen, 'red', (self.shift, self.shift + 90),
                         (self.shift + 720, self.shift + 90), 3)

    def draw_fields(self):
        for i in [30, 390]:
            pygame.draw.rect(self.screen, 'blue', (self.shift + i, self.shift + 120, 300, 300), 3)
        font = pygame.font.Font(None, 30)
        for j in [65, 425]:
            for i in range(1, 11):
                text = font.render(str(i), True, (0, 0, 255))
                self.screen.blit(text, (i * self.cell_size + j,
                                        3 * self.cell_size + self.shift + 5))
        string = 'абвгдеёжзик'
        for j in [0, 365]:
            for i in range(10):
                text = font.render(string[i], True, (0, 0, 255))
                self.screen.blit(text, (self.shift + 5 + j,
                                        (4 + i) * self.cell_size + self.shift + 5))


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('Морской бой')
    game = Game()
    pygame.quit()
