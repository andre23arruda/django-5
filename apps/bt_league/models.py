import math, random
from django.db import models
from itertools import combinations
from shortuuid.django_fields import ShortUUIDField


class Ranking(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Ranking'
        verbose_name_plural = 'Rankings'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Jogador(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Jogador'
        verbose_name_plural = 'Jogadores'
        ordering = ['nome']

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

        pontos, vitorias, saldo = 0, 0, 0
        for jogo in jogos:
            if jogo.placar_dupla1 is None or jogo.placar_dupla2 is None:
                continue
            elif (jogo.dupla1_jogador1 == self or jogo.dupla1_jogador2 == self):
                pontos_a_favor = jogo.placar_dupla1 or 0
                pontos_contra = jogo.placar_dupla2 or 0
                if jogo.placar_dupla1 > jogo.placar_dupla2:
                    vitorias += 1
            else:
                pontos_a_favor = jogo.placar_dupla2 or 0
                pontos_contra = jogo.placar_dupla1 or 0
                if jogo.placar_dupla1 < jogo.placar_dupla2:
                    vitorias += 1
            pontos += pontos_a_favor
            saldo += (pontos_a_favor - pontos_contra)
        return vitorias, pontos, saldo, len(jogos)

    def admin_ranking(self, torneio):
        vitorias, pontos, saldo, jogos = self.player_points(torneio)
        return -vitorias, -pontos, -saldo, self.nome


class Torneio(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    data = models.DateField()
    jogadores = models.ManyToManyField(Jogador, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    quadras = models.IntegerField(default=1, help_text='Quantidade de quadras para jogos simultâneos')
    ranking = models.ForeignKey(Ranking, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = 'Torneio'
        verbose_name_plural = 'Torneios'
        ordering = ['-data']

    def __str__(self):
        return self.nome

    def create_teams(self):
        '''Gera todas as duplas possíveis entre os jogadores'''
        todos_jogadores = list(self.jogadores.all())
        duplas = list(combinations(todos_jogadores, 2))
        return duplas

    def create_games(self):
        '''Gera jogos usando todas as duplas possíveis'''
        jogadores = list(self.jogadores.all())
        # random.shuffle(jogadores)
        n_jogadores = len(jogadores)
        excess_playes = n_jogadores % 4
        if excess_playes:
            return Exception(f'Não é possível gerar jogos com { n_jogadores } jogadores. Número de jogadores deve ser multiplo de 4.')

        quadras_jogadores = (n_jogadores / self.quadras) % 2
        if quadras_jogadores:
            return Exception(f'Não é possível gerar jogos para { self.quadras } quadras com { n_jogadores } jogadores.')

        if self.jogo_set.exists():
            self.jogo_set.all().delete()

        num_rodadas_total = n_jogadores - 1
        rodadas, partidas, jogos_gerados = [], [], []
        for rodada in range(num_rodadas_total):
            matches = []
            for i in range(n_jogadores // 2):
                matches.append((jogadores[i], jogadores[n_jogadores - 1 - i]))

            # Rotacionar jogadores exceto o primeiro
            jogadores = [jogadores[0]] + [jogadores[-1]] + jogadores[1:-1]
            rodadas.append(matches)

        for rodada in rodadas:
            for i in range(0, len(rodada), 2):
                if i + 1 < len(rodada):
                    partida = (rodada[i], rodada[i+1])
                    partidas.append(partida)

        # Distribuir partidas nas quadras
        partidas_por_rodada = self.quadras
        num_rodadas_necessarias = math.ceil(len(partidas) / partidas_por_rodada)
        for rodada in range(num_rodadas_necessarias):
            for quadra in range(1, self.quadras + 1):
                indice_partida = rodada * partidas_por_rodada + (quadra - 1)
                if indice_partida < len(partidas):
                    dupla1, dupla2 = partidas[indice_partida]
                    jogo = Jogo(
                        torneio=self,
                        quadra=quadra,
                        dupla1_jogador1=dupla1[0],
                        dupla1_jogador2=dupla1[1],
                        dupla2_jogador1=dupla2[0],
                        dupla2_jogador2=dupla2[1]
                    )
                    jogos_gerados.append(jogo)

        # if self.quadras == 1:
        #     random.shuffle(jogos_gerados)
        Jogo.objects.bulk_create(jogos_gerados)
        return jogos_gerados

    def has_games(self):
        return Jogo.objects.filter(torneio=self).exists()

    def finish(self):
        # self.jogadores.all().update(ativo=False)
        self.ativo = False
        self.save()


class Jogo(models.Model):
    torneio = models.ForeignKey(Torneio, on_delete=models.CASCADE)
    quadra = models.IntegerField(default=1)
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

    def save(self, *args, **kwargs):
        self.concluido = (
            self.placar_dupla1 is not None and
            self.placar_dupla1 != '' and
            self.placar_dupla2 is not None and
            self.placar_dupla2 != ''
        )
        super().save(*args, **kwargs)
