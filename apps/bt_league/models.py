import random
from django.db import models
from itertools import combinations


class Jogador(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Jogador'
        verbose_name_plural = 'Jogadores'

    def __str__(self):
        return self.nome

    def ranking(self, torneio):
        '''Calcula a posição do jogador no ranking de um torneio'''
        # Obtém todos os jogadores do torneio
        jogadores = torneio.jogadores.all()

        # Cria lista de tuplas (jogador, pontos)
        ranking = [(jogador, jogador.player_points(torneio)) for jogador in jogadores]

        # Ordena por pontos em ordem decrescente
        ranking_ordenado = sorted(ranking, key=lambda x: x[1], reverse=True)

        # Encontra a posição do jogador
        for posicao, (jogador, pontos) in enumerate(ranking_ordenado, 1):
            if jogador == self:
                return posicao

        return None

    def player_points(self, torneio=None):
        '''Calcula pontos do jogador em um torneio específico ou em todos os torneios'''
        jogos = Jogo.objects.filter(
            models.Q(dupla1_jogador1=self) | models.Q(dupla1_jogador2=self) |
            models.Q(dupla2_jogador1=self) | models.Q(dupla2_jogador2=self)
        )

        if torneio:
            jogos = jogos.filter(torneio=torneio)

        pontos = 0
        for jogo in jogos:
            if (jogo.dupla1_jogador1 == self or jogo.dupla1_jogador2 == self):
                jogo_pontos = jogo.placar_dupla1 or 0
            else:
                jogo_pontos = jogo.placar_dupla2 or 0
            pontos += jogo_pontos
        return pontos

    def player_victories(self, torneio=None):
        '''Calcula número de vitorias do jogador em um torneio específico ou em todos os torneios'''
        jogos = Jogo.objects.filter(
            models.Q(dupla1_jogador1=self) | models.Q(dupla1_jogador2=self) |
            models.Q(dupla2_jogador1=self) | models.Q(dupla2_jogador2=self)
        )

        if torneio:
            jogos = jogos.filter(torneio=torneio)

        vitorias = 0
        for jogo in jogos:
            if jogo.placar_dupla1 is None or jogo.placar_dupla2 is None:
                continue
            elif (jogo.dupla1_jogador1 == self or jogo.dupla1_jogador2 == self) and jogo.placar_dupla1 > jogo.placar_dupla2:
                vitorias += 1
            elif (jogo.dupla2_jogador1 == self or jogo.dupla2_jogador2 == self) and jogo.placar_dupla1 < jogo.placar_dupla2:
                vitorias += 1
        return vitorias


class Torneio(models.Model):
    nome = models.CharField(max_length=100)
    data = models.DateField()
    jogadores = models.ManyToManyField(Jogador)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    def create_teams(self):
        '''Gera todas as duplas possíveis entre os jogadores'''
        todos_jogadores = list(self.jogadores.all())
        duplas = list(combinations(todos_jogadores, 2))
        return duplas

    def create_games(self):
        '''Gera jogos usando todas as duplas possíveis'''
        if len(self.jogadores.all()) % 4 != 0:
            return Exception('Número de jogadores deve ser multiplo de 4')

        duplas = self.create_teams()
        random.shuffle(duplas)
        jogos_gerados = []

        while duplas:
            # Pega primeira dupla livre como primeira dupla do jogo
            dupla1 = duplas.pop()

            # Procura outra dupla que não tenha jogadores repetidos
            for i, dupla2 in enumerate(duplas):
                if (len(set(dupla1 + dupla2)) == 4):
                    # Criar jogo
                    jogo = Jogo.objects.create(
                        torneio=self,
                        dupla1_jogador1=dupla1[0],
                        dupla1_jogador2=dupla1[1],
                        dupla2_jogador1=dupla2[0],
                        dupla2_jogador2=dupla2[1]
                    )

                    jogos_gerados.append(jogo)
                    duplas.pop(i)
                    break

        return jogos_gerados


class Jogo(models.Model):
    torneio = models.ForeignKey(Torneio, on_delete=models.CASCADE)
    dupla1_jogador1 = models.ForeignKey(Jogador, related_name='dupla1_jogador1', on_delete=models.CASCADE)
    dupla1_jogador2 = models.ForeignKey(Jogador, related_name='dupla1_jogador2', on_delete=models.CASCADE)
    dupla2_jogador1 = models.ForeignKey(Jogador, related_name='dupla2_jogador1', on_delete=models.CASCADE)
    dupla2_jogador2 = models.ForeignKey(Jogador, related_name='dupla2_jogador2', on_delete=models.CASCADE)

    placar_dupla1 = models.IntegerField(null=True, blank=True, verbose_name='')
    placar_dupla2 = models.IntegerField(null=True, blank=True, verbose_name='')
    concluido = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.dupla1_jogador1.nome}/{self.dupla1_jogador2.nome} X {self.dupla2_jogador1.nome}/{self.dupla2_jogador2.nome}'

    def dupla_1(self):
        return f'{self.dupla1_jogador1.nome}/{self.dupla1_jogador2.nome}'

    def dupla_2(self):
        return f'{self.dupla2_jogador1.nome}/{self.dupla2_jogador2.nome}'
