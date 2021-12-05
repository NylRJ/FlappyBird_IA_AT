import pygame
import os
import random
import neat

AGENT = True
GENERATION = 0

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800

PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'Pipe.png')))

FLOOR_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))

IMAGE_BACKGROUND = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))

BIRD_IMAGES = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png'))),
]

pygame.font.init()
FONTE_PONTOS = pygame.font.SysFont('arial', 30)


class Bird:
    IMGS = BIRD_IMAGES
    # Animação/Rotação
    MAXIMUM_ROTATION = 25
    SPEED_ROTATION = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.velocity = 0
        self.height = self.y
        self.time = 0
        self.cont_image = 0
        self.image = self.IMGS[0]

    def saltar(self):
        self.velocity = -10.5
        self.time = 0
        self.height = self.y

    def mover(self):
        # Δx
        self.time += 1

        # S = so + vot + at²/2
        displacement = 1.5 * (self.time ** 2) + self.velocity * self.time

        if displacement > 16:
            displacement = 16
        elif displacement < 0:
            displacement -= 0.5

        self.y += displacement

        if displacement < 0 or self.y < (self.height + 50):
            if self.angle < self.MAXIMUM_ROTATION:
                self.angle = self.MAXIMUM_ROTATION
        else:
            if self.angle > 90:
                self.angle -= self.SPEED_ROTATION

    def desenhar(self, tela):
        # definir  image atual do passaro
        self.cont_image += 1

        if self.cont_image < self.ANIMATION_TIME:
            self.image = self.IMGS[0]
        elif self.cont_image < self.ANIMATION_TIME * 2:
            self.image = self.IMGS[1]
        elif self.cont_image < self.ANIMATION_TIME * 3:
            self.image = self.IMGS[2]
        elif self.cont_image < self.ANIMATION_TIME * 4:
            self.image = self.IMGS[1]
        elif self.cont_image >= self.ANIMATION_TIME * 4 + 1:
            self.image = self.IMGS[0]
            self.cont_image = 0

        # para de bater asa
        if self.angle <= -80:
            self.image = self.IMGS[1]
            self.cont_image = self.ANIMATION_TIME * 2

        # desenhar a image
        imagem_rotacionada = pygame.transform.rotate(self.image, self.angle)
        pos_centro_imagem = self.image.get_rect(topleft=(self.x, self.y)).center
        retangulo = imagem_rotacionada.get_rect(center=pos_centro_imagem)
        tela.blit(imagem_rotacionada, retangulo.topleft)

    # criando uma matriz de pixel para detectar a colição
    def get_mask(self):
        return pygame.mask.from_surface(self.image)


class Pipe:
    DISTANCE = 200
    VELOCITY = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.pos_topo = 0
        self.pos_base = 0
        self.CANO_TOP = pygame.transform.flip(PIPE_IMAGE, False, True)
        self.CANO_LOW = PIPE_IMAGE
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.pos_topo = self.height - self.CANO_TOP.get_height()
        self.pos_base = self.height + self.DISTANCE

    def mover(self):
        self.x -= self.VELOCITY

    def desenhar(self, tela):
        tela.blit(self.CANO_TOP, (self.x, self.pos_topo))
        tela.blit(self.CANO_LOW, (self.x, self.pos_base))

    def colidiu(self, passaro):
        passaro_mask = passaro.get_mask()
        topo_mask = pygame.mask.from_surface(self.CANO_TOP)
        base_mask = pygame.mask.from_surface(self.CANO_LOW)

        distancia_topo = (round(self.x) - round(passaro.x), round(self.pos_topo) - round(passaro.y))
        distancia_base = (round(self.x) - round(passaro.x), round(self.pos_base) - round(passaro.y))

        topo_ponto = passaro_mask.overlap(topo_mask, distancia_topo)
        base_ponto = passaro_mask.overlap(base_mask, distancia_base)

        if topo_ponto or base_ponto:
            return True
        else:
            return False


class Chao:
    VELOCIDADE = 5
    LARGURA = FLOOR_IMAGE.get_width()
    IMAGEM = FLOOR_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.LARGURA

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x2 + self.LARGURA
        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(self.IMAGEM, (self.x1, self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))


def desenhar_tela(tela, passaros, canos, chao, pontos):  # return fitness
    tela.blit(IMAGE_BACKGROUND, (0, 0))
    for passaro in passaros:
        passaro.desenhar(tela)
    for cano in canos:
        cano.desenhar(tela)

    texto = FONTE_PONTOS.render(f"Pontuação: {pontos}", 1, (255, 255, 255))
    tela.blit(texto, (SCREEN_WIDTH - 10 - texto.get_width(), 10))

    if AGENT:
        texto = FONTE_PONTOS.render(f"Geração: {GENERATION}", 1, (255, 255, 255))
        tela.blit(texto, (10, 10))

    chao.desenhar(tela)
    pygame.display.update()


def fitness(genomas, config):  # que contem o fitness
    global GENERATION
    GENERATION += 1

    if AGENT:
        listnetwork_list = []
        list_genomas = []
        bird_list = []
        for _, genoma in genomas:
            # create rede neual
            rede = neat.nn.FeedForwardNetwork.create(genoma, config)
            listnetwork_list.append(rede)
            genoma.fitness = 0
            list_genomas.append(genoma)
            bird_list.append(Bird(230, 350))
    else:
        bird_list = [Bird(230, 30)]
    chao = Chao(730)
    canos = [Pipe(700)]
    tela = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pontos = 0
    relogio = pygame.time.Clock()

    rodando = True
    while rodando:
        relogio.tick(30)

        # interação com o jogo
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
                pygame.quit()
                quit()
            if not AGENT:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        for bird in bird_list:
                            bird.saltar()
        # deefinir o comportamento do agent para qual cano o passaro deve olhar
        index_cano = 0
        if len(bird_list) > 0:
            if len(canos) > 1 and bird_list[0].x > (canos[0].x + canos[0].CANO_TOP.get_width()):
                index_cano = 1
        else:
            rodando = False
            break

        # O agente percebe a o anbiente e executa a ação
        for i, passaro in enumerate(bird_list):
            passaro.mover()
            if AGENT:
                # a cada mover incremento o fitness do passaro
                list_genomas[i].fitness += 0.1
                # defino se o passaro pula ou não
                # -1 e 1 -> se o output > 0.5 então passaro pula
                output = listnetwork_list[i].activate(
                    (passaro.y, abs(passaro.y - canos[index_cano].height), abs(passaro.y - canos[index_cano].pos_base)))
                if output[0] > 0.5:
                    passaro.saltar()

        chao.mover()
        # verifico se o passaro já passed e pontuo

        adicionar_cano = False
        remover_canos = []
        for cano in canos:
            for i, passaro in enumerate(bird_list):
                if cano.colidiu(passaro):
                    bird_list.pop(i)
                    # aplico a penalidáde
                    if AGENT:
                        list_genomas[i].fitness -= 1
                        list_genomas.pop(i)
                        listnetwork_list.pop(i)
                if not cano.passed and passaro.x > cano.x:
                    cano.passed = True
                    adicionar_cano = True
            cano.mover()
            if cano.x + cano.CANO_TOP.get_width() < 0:
                remover_canos.append(cano)

        if adicionar_cano:
            pontos += 1
            canos.append(Pipe(600))
            # dou recompensa
            for genoma in list_genomas:
                genoma.fitness += 5
        for cano in remover_canos:
            canos.remove(cano)

        for i, passaro in enumerate(bird_list):
            if (passaro.y + passaro.image.get_height()) > chao.y or passaro.y < 0:
                bird_list.pop(i)
                if AGENT:
                    list_genomas.pop(i)
                    listnetwork_list.pop(i)

        desenhar_tela(tela, bird_list, canos, chao, pontos)


def rodar(pathConfig):
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                pathConfig
                                )
    populacao = neat.Population(config)
    populacao.add_reporter(neat.StdOutReporter(True))
    populacao.add_reporter(neat.StatisticsReporter())

    if AGENT:
        populacao.run(fitness, 50)
    else:
        fitness(None, None)


if __name__ == '__main__':
    path = os.path.dirname(__file__)
    path_config = os.path.join(path, 'config.txt')
    rodar(path_config)
