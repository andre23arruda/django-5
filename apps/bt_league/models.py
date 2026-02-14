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
    slug = models.SlugField(null=False, unique=True)

    class Meta:
        verbose_name = 'Ranking'
        verbose_name_plural = 'Rankings'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f'{slugify(self.nome)}_{self.id}'
        return super().save(*args, **kwargs)


class Jogador(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=11, blank=True, null=True)
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
    inscricao_aberta = models.BooleanField(
        default=False,
        verbose_name='Inscrição aberta',
        help_text='Criar um link para cadastrar jogadores no torneio'
    )

    class Meta:
        verbose_name = 'Campeonato'
        verbose_name_plural = 'Campeonatos'
        ordering = ['-data', '-criado_em']

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
        jogos_gerados = []

        # Algoritmo de rotação (Circle Method) adaptado para duplas e confrontos
        for r in range(num_rodadas_total):
            # Rotaciona os jogadores mantendo o primeiro fixo
            atual = [jogadores[0]] + jogadores[-r:] + jogadores[1:-r] if r > 0 else jogadores

            # Divide os jogadores em duplas e depois em jogos (A&B vs C&D)
            # Para cada jogo na rodada, criamos o objeto Jogo
            # A 'quadra' será usada para armazenar o número da rodada
            for i in range(0, n_jogadores, 4):
                p1, p2, p3, p4 = atual[i], atual[i+1], atual[i+2], atual[i+3]

                jogo = Jogo(
                    torneio=self,
                    quadra=r + 1,
                    dupla1_jogador1=p1,
                    dupla1_jogador2=p2,
                    dupla2_jogador1=p3,
                    dupla2_jogador2=p4
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
    dupla1_jogador1 = models.ForeignKey(Jogador, related_name='dupla1_jogador1', on_delete=models.CASCADE, verbose_name='Jogador 1 dupla 1')
    dupla1_jogador2 = models.ForeignKey(Jogador, related_name='dupla1_jogador2', on_delete=models.CASCADE, verbose_name='Jogador 2 dupla 1')
    dupla2_jogador1 = models.ForeignKey(Jogador, related_name='dupla2_jogador1', on_delete=models.CASCADE, verbose_name='Jogador 1 dupla 2')
    dupla2_jogador2 = models.ForeignKey(Jogador, related_name='dupla2_jogador2', on_delete=models.CASCADE, verbose_name='Jogador 2 dupla 2')
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
