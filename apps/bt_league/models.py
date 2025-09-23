import math, random
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from shortuuid.django_fields import ShortUUIDField

GAME_STATUS = (
    ('P', '🚫'),
    ('A', '🎾'),
    ('C', '✅'),
)

class Ranking(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    grupo_criador = models.ForeignKey('auth.Group', on_delete=models.SET_NULL, null=True, blank=True)
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
    grupo_criador = models.ForeignKey('auth.Group', on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Jogador'
        verbose_name_plural = 'Jogadores'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def short_name(self):
        name_split = self.nome.split(' ')
        if len(name_split) > 1:
            return name_split[0][0] + '. ' + name_split[1]
        else:
            return name_split[0]

    def ranking(self, torneio):
        '''Calcula a posição do jogador no ranking de um torneio'''
        jogadores = torneio.jogadores.all()
        ranking = [(jogador, jogador.player_points(torneio)) for jogador in jogadores]
        ranking_ordenado = sorted(ranking, key=lambda x: x[1], reverse=True)
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

        pontos, vitorias, saldo, n_jogos = 0, 0, 0, 0
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
            n_jogos += 1
        return vitorias, pontos, saldo, n_jogos

    def admin_ranking(self, torneio):
        vitorias, pontos, saldo, jogos = self.player_points(torneio)
        return -vitorias, -pontos, -saldo, self.nome


class Torneio(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    data = models.DateField()
    jogadores = models.ManyToManyField(Jogador, blank=True, help_text='O número de jogadores deve ser multiplo de 4.')
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    grupo_criador = models.ForeignKey('auth.Group', on_delete=models.SET_NULL, null=True, blank=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    quadras = models.IntegerField(default=1, help_text='Quantidade de quadras para jogos simultâneos')
    ranking = models.ForeignKey(Ranking, on_delete=models.SET_NULL, blank=True, null=True, help_text='Agrupar torneio em um ranking')
    slug = models.SlugField(null=False, unique=True)

    class Meta:
        verbose_name = 'Campeonato'
        verbose_name_plural = 'Campeonatos'
        ordering = ['-data']

    def __str__(self):
        return self.nome

    def shuffle_players(self):
        SEED = 42
        jogadores = list(self.jogadores.all())
        random.seed(SEED)
        random.shuffle(jogadores)
        return jogadores

    def create_games(self):
        '''Gera jogos usando todas as duplas possíveis'''
        jogadores = self.shuffle_players()
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

        Jogo.objects.bulk_create(jogos_gerados)
        return jogos_gerados

    def has_games(self):
        return self.jogo_set.filter(torneio=self).exists()

    def finish(self):
        # self.jogadores.all().update(ativo=False)
        self.ativo = False
        self.save()

    def is_finished(self):
        jogos = self.jogo_set.all().exclude(concluido='C').count()
        if jogos > 0:
            return False
        return True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f'{slugify(self.nome)}_{self.id}'
        return super().save(*args, **kwargs)


class Jogo(models.Model):
    torneio = models.ForeignKey(Torneio, on_delete=models.CASCADE)
    quadra = models.IntegerField(default=1)
    dupla1_jogador1 = models.ForeignKey(Jogador, related_name='dupla1_jogador1', on_delete=models.CASCADE)
    dupla1_jogador2 = models.ForeignKey(Jogador, related_name='dupla1_jogador2', on_delete=models.CASCADE)
    dupla2_jogador1 = models.ForeignKey(Jogador, related_name='dupla2_jogador1', on_delete=models.CASCADE)
    dupla2_jogador2 = models.ForeignKey(Jogador, related_name='dupla2_jogador2', on_delete=models.CASCADE)
    placar_dupla1 = models.IntegerField(null=True, blank=True, verbose_name='Pontos dupla 1')
    placar_dupla2 = models.IntegerField(null=True, blank=True, verbose_name='Pontos dupla 2')
    concluido = models.CharField(max_length=2, default='P', choices=GAME_STATUS, verbose_name='Status')

    def __str__(self):
        return f'{self.dupla1_jogador1.short_name()}/{self.dupla1_jogador2.short_name()} X {self.dupla2_jogador1.short_name()}/{self.dupla2_jogador2.short_name()}'

    def dupla_1(self):
        return mark_safe(f'<span>{self.dupla1_jogador1.short_name()}<br/>{self.dupla1_jogador2.short_name()}</span>')

    def dupla_2(self):
        return mark_safe(f'<span>{self.dupla2_jogador1.short_name()}<br/>{self.dupla2_jogador2.short_name()}</span>')

    def render_dupla_1(self):
        return f'{self.dupla1_jogador1}\n{self.dupla1_jogador2}'

    def render_dupla_2(self):
        return f'{self.dupla2_jogador1}\n{self.dupla2_jogador2}'

    def save(self, *args, **kwargs):
        finished = (
            self.placar_dupla1 is not None and
            self.placar_dupla1 != '' and
            self.placar_dupla2 is not None and
            self.placar_dupla2 != ''
        )
        if finished:
            self.concluido = 'C'
        elif self.concluido == 'A':
            self.concluido = 'A'
        else:
            self.concluido = 'P'
        super().save(*args, **kwargs)
