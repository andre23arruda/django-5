import random
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.html import format_html
from itertools import zip_longest
from shortuuid.django_fields import ShortUUIDField
from .utils import FUTEVOLEI_TEMPLATES

FASE_CHOICES = [
    ('FASE 1', 'F1'),
    ('FASE 2', 'F2'),
    ('FASE 3', 'F3'),
    ('FASE 4', 'F4'),
    ('FASE 5', 'F5'),
    ('FASE 6', 'F6'),
    ('FASE 7', 'F7'),
    ('FASE 8', 'F8'),
]
QUANTIDADE_TIMES = [
    (4, '4'),
    (8, '8'),
    (16, '16'),
]
GAME_STATUS = (
    ('P', '🚫'),
    ('A', '🎾'),
    ('C', '✅'),
)
TORNEIO_TIPO_CHOICES = (
    ('S', 'Simples'),
    ('D', 'Duplas')
)


class Jogador(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=11, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    jogos = models.IntegerField(default=0)
    vitorias = models.IntegerField(default=0, verbose_name='Vitórias')
    derrotas = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_por = models.ForeignKey(
        'auth.User',
        related_name='jogadores_futevolei_criados',
        on_delete=models.SET_NULL,
        null=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Jogador'
        verbose_name_plural = 'Jogadores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Dupla(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    jogador1 = models.ForeignKey(
        'Jogador',
        on_delete=models.CASCADE,
        related_name='jogador1',
        verbose_name='Jogador 1',
        null=True,
        blank=True
    )
    jogador2 = models.ForeignKey(
        'Jogador',
        on_delete=models.CASCADE,
        related_name='jogador2',
        verbose_name='Jogador 2',
        null=True,
        blank=True
    )
    torneio = models.ForeignKey('Torneio', related_name='duplas', on_delete=models.CASCADE)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_por = models.ForeignKey(
        'auth.User',
        related_name='duplas_futevolei_criadas',
        on_delete=models.SET_NULL,
        null=True
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dupla'
        verbose_name_plural = 'Duplas'
        ordering = ['jogador1__nome']

    def __str__(self):
        if not self.jogador2:
            return f'{self.jogador1}'
        return f'{self.jogador1}/{self.jogador2}'

    def save(self, *args, **kwargs):
        return super(Dupla, self).save(*args, **kwargs)

    def render(self):
        if not self.jogador2:
            return f'{ self.jogador1 }'
        return format_html('{}<br/>{}', self.jogador1, self.jogador2)

    def render_special(self):
        if not self.jogador2:
            return f'{self.jogador1}'
        return f'{self.jogador1}\n{self.jogador2}'

    def get_group(self, torneio):
        '''Retorna o grupo no qual a dupla está jogando em um torneio específico.'''
        jogos = Jogo.objects.filter(
            torneio=torneio,
            fase__startswith='GRUPO',
        ).filter(
            models.Q(dupla1=self) | models.Q(dupla2=self)
        )

        if jogos.exists():
            return jogos.first().fase
        return None

    def get_group_data(self, torneio):
        '''Retorna estatísticas da dupla no grupo (posição, vitórias e pontos)'''
        grupo = self.get_group(torneio)
        if not grupo:
            return 0, 0, 0, 0

        jogos_grupo = Jogo.objects.filter(
            torneio=torneio,
            fase=grupo,
        )

        # Processar jogos do grupo para calcular vitórias e pontos
        estatisticas = {}
        for jogo in jogos_grupo:
            if jogo.pontos_dupla1 is not None and jogo.pontos_dupla2 is not None:
                estatisticas[jogo.dupla1] = estatisticas.get(jogo.dupla1, {'vitorias': 0, 'pontos': 0, 'grupo': int(grupo[6:])})
                estatisticas[jogo.dupla2] = estatisticas.get(jogo.dupla2, {'vitorias': 0, 'pontos': 0, 'grupo': int(grupo[6:])})

                if jogo.pontos_dupla1 > jogo.pontos_dupla2:
                    estatisticas[jogo.dupla1]['vitorias'] += 1
                elif jogo.pontos_dupla2 > jogo.pontos_dupla1:
                    estatisticas[jogo.dupla2]['vitorias'] += 1

                estatisticas[jogo.dupla1]['pontos'] += jogo.pontos_dupla1
                estatisticas[jogo.dupla2]['pontos'] += jogo.pontos_dupla2

        # Ordenar duplas pelo número de vitórias e pontos (desempate)
        ranking = sorted(estatisticas.items(), key=lambda x: (-x[1]['vitorias'], -x[1]['pontos']))

        # Determinar posição, vitórias e pontos da dupla
        for pos, (dupla, stats) in enumerate(ranking, start=1):
            if dupla == self:
                return -stats['grupo'], -pos, stats['vitorias'], stats['pontos']

        # Caso algo dê errado (não deveria)
        return 0, 0, 0, 0


class Torneio(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    data = models.DateField()
    quantidade_times = models.IntegerField(
        choices=QUANTIDADE_TIMES,
        default=8,
        verbose_name='Nº de times',
    )
    tipo = models.CharField(
        max_length=1,
        choices=TORNEIO_TIPO_CHOICES,
        default='D',
        verbose_name='Tipo de Torneio',
        help_text='Simples ou Duplas'
    )
    slug = models.SlugField(null=False, unique=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_por = models.ForeignKey(
        'auth.User',
        related_name='torneios_futevolei',
        on_delete=models.SET_NULL,
        null=True
    )
    draw_pairs = models.BooleanField(
        default=False,
        verbose_name='Duplas aleatórias',
        help_text='Duplas montadas aleatoriamente ao criar os jogos'
    )
    inscricao_aberta = models.BooleanField(
        default=False,
        verbose_name='Inscrição aberta',
        help_text='Criar um link para cadastrar jogadores no torneio'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Torneio'
        verbose_name_plural = 'Torneios'
        ordering = ['-data', '-criado_em']

    def __str__(self):
        return self.nome

    def get_sorted_games(self, queryset):
        '''Organiza os jogos em ordem de grupos e fases'''
        if self.quantidade_times > 1:
            ids_playoff = list(queryset.annotate(
                fase_order=models.Case(
                    models.When(fase='FASE 1', then=0),
                    models.When(fase='FASE 2', then=1),
                    models.When(fase='FASE 3', then=2),
                    models.When(fase='FASE 4', then=3),
                    models.When(fase='FASE 5', then=4),
                    models.When(fase='FASE 6', then=5),
                    models.When(fase='FASE 7', then=6),
                    models.When(fase='FASE 8', then=7),
                    default=99,
                    output_field=models.IntegerField()
                )
            ).order_by('fase_order', 'id').values_list('id', flat=True))

            return queryset.filter(id__in=ids_playoff).annotate(
                custom_order=models.Case(
                    *[models.When(id=id_val, then=pos) for pos, id_val in enumerate(ids_playoff)],
                    output_field=models.IntegerField()
                )
            ).order_by('custom_order')

    def shuffle_teams(self) -> list:
        if self.draw_pairs and self.tipo == 'D':
            jogadores = [jogador for dupla in self.duplas.all() for jogador in [dupla.jogador1, dupla.jogador2] if jogador]
            random.shuffle(jogadores)
            duplas = []
            self.duplas.all().delete()
            for i in range(0, len(jogadores), 2):
                duplas.append(Dupla.objects.create(
                    jogador1=jogadores[i],
                    jogador2=jogadores[i + 1],
                    torneio=self)
                )
        else:
            duplas = list(self.duplas.all())
        SEED = 42
        random.seed(SEED)
        random.shuffle(duplas)
        return duplas

    def create_games(self) -> list:        
        template = FUTEVOLEI_TEMPLATES.get(self.quantidade_times)
        if not template:
            return []

        if self.jogo_set.exists():
            self.jogo_set.all().delete()
            
        # Embaralha ou organiza as duplas
        duplas = self.shuffle_teams()
        jogos_criados = []

        for fase_nome, jogos in template.items():
            for j in jogos:
                dupla1 = None
                dupla2 = None

                # Se for a Fase 1, atribuímos as duplas iniciais
                if fase_nome == 'FASE 1':
                    idx1 = int(j['dupla1']) - 1
                    idx2 = int(j['dupla2']) - 1
                    dupla1 = duplas[idx1] if idx1 < len(duplas) else None
                    dupla2 = duplas[idx2] if idx2 < len(duplas) else None

                # Criar o objeto Jogo no banco
                novo_jogo = Jogo.objects.create(
                    torneio=self,
                    dupla1=dupla1,
                    dupla2=dupla2,
                    fase=fase_nome.split(' (')[0], # Limpa o nome caso tenha parênteses
                    playoff_number=j['jogo'],
                    playoff_help_text=f"{j['dupla1']} x {j['dupla2']}"
                )
                jogos_criados.append(novo_jogo)
        
        return jogos_criados

    def next_stage(self) -> bool:
        '''Analisa jogos concluídos e move W (Winners) e L (Losers) para os próximos jogos'''
        template = FUTEVOLEI_TEMPLATES.get(self.quantidade_times)
        
        # Pegamos todos os jogos concluídos do torneio
        jogos_concluidos = self.jogo_set.filter(concluido='C')
        
        for jogo_atual in jogos_concluidos:
            # Identificamos quem venceu e quem perdeu
            vencedor = jogo_atual.vencedor
            perdedor = jogo_atual.dupla1 if jogo_atual.vencedor == jogo_atual.dupla2 else jogo_atual.dupla2
            
            # Marcadores que procuramos no help_text dos jogos futuros
            target_w = f"Vencedor Jogo {jogo_atual.playoff_number}"
            target_l = f"Perdedor Jogo {jogo_atual.playoff_number}"

            # Procurar jogos que dependem do resultado deste jogo
            jogos_futuros = self.jogo_set.filter(
                models.Q(playoff_help_text__contains=target_w) | 
                models.Q(playoff_help_text__contains=target_l)
            ).exclude(concluido='C')

            for proximo in jogos_futuros:
                updated = False
                ajuda = proximo.playoff_help_text.split(' x ')
                
                # Lógica para posicionar o Vencedor (W)
                if target_w in ajuda:
                    if ajuda[0] == target_w:
                        proximo.dupla1 = vencedor
                    else:
                        proximo.dupla2 = vencedor
                    updated = True
                
                # Lógica para posicionar o Perdedor (L)
                if target_l in ajuda:
                    if ajuda[0] == target_l:
                        proximo.dupla1 = perdedor
                    else:
                        proximo.dupla2 = perdedor
                    updated = True
                
                if updated:
                    proximo.save()

        return True

    def finish(self) -> None:
        self.ativo = False
        self.save()

    def is_finished(self) -> bool:
        jogos = self.jogo_set.all().exclude(concluido='C').count()
        if jogos > 0:
            return False
        return True

    def has_games(self) -> bool:
        return self.jogo_set.exists()

    def team_title(self, number='') -> str:
        '''Retorna o cabeçalho de dupla ou jogador'''
        TIPO = {
            'S': 'Jogador',
            'D': 'Dupla',
        }
        return f'{TIPO[self.tipo]} {number}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f'{slugify(self.nome)}_{self.id}'
        return super().save(*args, **kwargs)


class Jogo(models.Model):
    torneio = models.ForeignKey('Torneio', on_delete=models.CASCADE, verbose_name='Torneio')
    dupla1 = models.ForeignKey('Dupla', related_name='dupla1', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Dupla 1')
    pontos_dupla1 = models.IntegerField(null=True, blank=True, verbose_name='Pontos dupla 1')
    dupla2 = models.ForeignKey('Dupla', related_name='dupla2', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Dupla 2')
    pontos_dupla2 = models.IntegerField(null=True, blank=True, verbose_name='Pontos dupla 2')
    vencedor = models.ForeignKey('Dupla', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Vencedor')
    fase = models.CharField(choices=FASE_CHOICES, default='GRUPO 1', max_length=100, null=True, blank=True, verbose_name='Fase')
    concluido = models.CharField(max_length=2, default='P', choices=GAME_STATUS, verbose_name='Status')
    obs = models.TextField(null=True, blank=True, help_text='Alguma observação sobre o jogo. Ex: "Dupla 1 WO"')
    playoff_number = models.SmallIntegerField(null=True, blank=True, verbose_name='Playoff game number')
    playoff_help_text = models.CharField(
        max_length=100, 
        default='', 
        blank=True, 
        verbose_name='Texto de ajuda para o playoff', 
        help_text='Ex: 1º G1x2º G2, 1º G2xBYE' 
    )

    def __str__(self):
        if self.dupla1 is None and self.dupla2 is None:
            return 'A definir'
        return f'{self.dupla1} X {self.dupla2}'

    def help_text(self, index) -> str:
        help_text = self.playoff_help_text or ''
        help_text = help_text.split('x')
        if index == 0:
            return help_text[0]
        return help_text[1]

    def placar(self) -> str:
        if self.pontos_dupla1 is None and self.pontos_dupla2 is None:
            return ''
        return f'{self.pontos_dupla1} X {self.pontos_dupla2}'

    def save(self, *args, **kwargs):
        if self.dupla1 is None and self.dupla2 is None:
            self.pontos_dupla1 = None
            self.pontos_dupla2 = None

        finished = (
            self.pontos_dupla1 is not None and
            self.pontos_dupla1 != '' and
            self.pontos_dupla2 is not None and
            self.pontos_dupla2 != ''
        )
        if finished:
            self.concluido = 'C'
            if self.pontos_dupla1 > self.pontos_dupla2:
                self.vencedor = self.dupla1
            elif self.pontos_dupla2 > self.pontos_dupla1:
                self.vencedor = self.dupla2
        elif self.concluido == 'A':
            self.concluido = 'A'
        else:
            self.concluido = 'P'
        super().save(*args, **kwargs)

    @property
    def winner(self):
        if self.pontos_dupla1 is not None and self.pontos_dupla2 is not None:
            if self.pontos_dupla1 > self.pontos_dupla2:
                return self.dupla1
            elif self.pontos_dupla2 > self.pontos_dupla1:
                return self.dupla2
        return None
