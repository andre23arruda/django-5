import random
from django.db import models
from itertools import combinations
from shortuuid.django_fields import ShortUUIDField


class Jogador(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
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
        vitorias = 0
        for jogo in jogos:
            if jogo.placar_dupla1 is None or jogo.placar_dupla2 is None:
                continue
            elif (jogo.dupla1_jogador1 == self or jogo.dupla1_jogador2 == self):
                jogo_pontos = jogo.placar_dupla1 or 0
                if jogo.placar_dupla1 > jogo.placar_dupla2:
                    vitorias += 1
            else:
                jogo_pontos = jogo.placar_dupla2 or 0
                if jogo.placar_dupla1 < jogo.placar_dupla2:
                    vitorias += 1
            pontos += jogo_pontos
        return vitorias, pontos


class Torneio(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    data = models.DateField()
    jogadores = models.ManyToManyField(Jogador, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    ativo = models.BooleanField(default=True)
    quadras = models.IntegerField(default=1)

    def __str__(self):
        return self.nome

    def create_teams(self):
        '''Gera todas as duplas possíveis entre os jogadores'''
        todos_jogadores = list(self.jogadores.all())
        duplas = list(combinations(todos_jogadores, 2))
        return duplas

    def create_games(self):
        '''Gera jogos usando todas as duplas possíveis'''
        n_jogadores = self.jogadores.count()
        excess_playes = n_jogadores % 4
        if excess_playes:
            return Exception(f'Não é possível gerar jogos com { n_jogadores } jogadores. Número de jogadores deve ser multiplo de 4.')

        quadras_jogadores = (n_jogadores / self.quadras) % 4
        if quadras_jogadores:
            return Exception(f'Não é possível gerar jogos para { self.quadras } quadras com { n_jogadores } jogadores.')

        if self.jogo_set.exists():
            self.jogo_set.all().delete()

        duplas = self.create_teams()
        jogos_gerados = []
        jogadores_por_quadra = []

        while duplas:
            for quadra in range(1, self.quadras + 1):
                if quadra == 1:
                    dupla1 = duplas.pop(0)
                else:
                    duplas_filtradas = [dupla for dupla in duplas if (dupla[0].id not in jogadores_por_quadra and dupla[1].id not in jogadores_por_quadra)]
                    dupla1 = duplas_filtradas.pop(0)
                    duplas.remove(dupla1)
                jogadores_por_quadra.extend([dupla1[0].id, dupla1[1].id])

                # Procura uma dupla2 que não tenha jogadores repetidos e não esteja jogando
                for i, dupla2 in enumerate(duplas):
                    if (len(set(dupla1 + dupla2)) == 4 and (dupla2[0].id not in jogadores_por_quadra and dupla2[1].id not in jogadores_por_quadra)):

                        jogo = Jogo(
                            torneio=self,
                            quadra=quadra,
                            dupla1_jogador1=dupla1[0],
                            dupla1_jogador2=dupla1[1],
                            dupla2_jogador1=dupla2[0],
                            dupla2_jogador2=dupla2[1]
                        )

                        # Atualiza o conjunto de jogadores na quadra
                        jogadores_por_quadra.extend([dupla2[0].id, dupla2[1].id])
                        jogos_gerados.append(jogo)
                        duplas.pop(i)
                        break

            jogadores_por_quadra =[]

        if self.quadras == 1:
            random.shuffle(jogos_gerados)
        for jogo in jogos_gerados:
            jogo.save()
        return jogos_gerados

    def has_games(self):
        return Jogo.objects.filter(torneio=self).exists()

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
        if self.placar_dupla1 is not None and self.placar_dupla2 is not None:
            self.concluido = True
        super().save(*args, **kwargs)
