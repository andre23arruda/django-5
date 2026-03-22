import random
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.html import format_html
from itertools import zip_longest
from shortuuid.django_fields import ShortUUIDField
from .utils import GROUPS_TEMPLATES

FASE_CHOICES = [
    ('GRUPO 1', 'G1'),
    ('GRUPO 2', 'G2'),
    ('GRUPO 3', 'G3'),
    ('GRUPO 4', 'G4'),
    ('GRUPO 5', 'G5'),
    ('GRUPO 6', 'G6'),
    ('GRUPO 7', 'G7'),
    ('GRUPO 8', 'G8'),
    ('OITAVAS', 'OF'),
    ('QUARTAS', 'QF'),
    ('SEMIFINAIS', 'SF'),
    ('FINAL', 'F'),
    ('TERCEIRO LUGAR', 'T'),
    ('CAMPEAO', 'C'),
]
QUANTIDADE_GRUPOS_CHOICES = [
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5'),
    (6, '6'),
    (7, '7'),
    (8, '8')
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
        related_name='jogadores_criados',
        on_delete=models.SET_NULL,
        null=True
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
        related_name='duplas_criadas',
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
        # torneio = self.torneio
        # duplas = torneio.duplas.all()
        # jogador1 = self.jogador1
        # jogador2 = self.jogador2
        # torneio_jogadores = list(duplas.values_list('jogador1', 'jogador2'))
        # jogadores = [x for xs in torneio_jogadores for x in xs if x is not None]
        # if jogador1.id not in jogadores and jogador2.id not in jogadores:
        #     return super(Dupla, self).save(*args, **kwargs)
        # return 'Jogador já cadastrado em outra dupla'

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
    quantidade_grupos = models.IntegerField(
        choices=QUANTIDADE_GRUPOS_CHOICES,
        default=2,
        verbose_name='Nº grupos',
        help_text=format_html('''
            Selecione o número de grupos para distribuir as duplas
            <ul>
                <li>1 grupo: Fase de grupo e FINAL</li>
                <li>2 grupos: Fase de grupo, SEMIFINAIS e FINAL</li>
                <li>3 ou 4 grupos: Fase de grupo, QUARTAS, SEMIFINAIS e FINAL</li>
                <li>5, 6, 7 ou 8 grupos: Fase de grupo, OITAVAS, QUARTAS, SEMIFINAIS e FINAL</li>
            </ul>
        ''')
    )
    tipo = models.CharField(
        max_length=1,
        choices=TORNEIO_TIPO_CHOICES,
        default='D',
        verbose_name='Tipo de Torneio',
        help_text='Simples ou Duplas'
    )
    playoffs = models.BooleanField(
        default=True,
        verbose_name='Playoffs',
        help_text='Ativar para criar jogos de playoffs (OITAVAS, QUARTAS, SEMIFINAIS e FINAL)'
    )
    terceiro_lugar = models.BooleanField(
        default=False,
        verbose_name='Terceiro lugar',
        help_text='É necessário 2 grupos ou mais.'
    )
    open = models.BooleanField(
        default=False,
        verbose_name='Criar jogos manualmente',
        help_text='Ativar para criar jogos manualmente (Apenas um grupo, sem playoffs)'
    )
    ranking = models.ForeignKey(
        'Ranking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Agrupar torneio em um ranking'
    )
    slug = models.SlugField(null=False, unique=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_por = models.ForeignKey(
        'auth.User',
        related_name='torneios',
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

    def create_groups(self, duplas) -> list | Exception:
        '''Distribui duplas em grupos de forma aleatória'''
        if len(duplas) < self.quantidade_grupos:
            return Exception(f'Número de duplas é menor que número de grupos')
        elif (len(duplas) // self.quantidade_grupos) < 2:
            return Exception(f'Número de duplas insuficientes para {self.quantidade_grupos} grupos')

        # Tamanho base de cada grupo e duplas extras
        tamanho_base = len(duplas) // self.quantidade_grupos
        duplas_extras = len(duplas) % self.quantidade_grupos

        # Distribui duplas nos grupos
        grupos = []
        posicao_atual = 0
        for i in range(self.quantidade_grupos):
            # Se ainda houver duplas extras, adiciona um a mais neste grupo
            tamanho_grupo = tamanho_base + (1 if i < duplas_extras else 0)

            # Pega os duplas para este grupo
            grupo = duplas[posicao_atual:posicao_atual + tamanho_grupo]
            grupos.append(grupo)
            posicao_atual += tamanho_grupo

        return grupos

    def create_games(self) -> list | Exception:
        '''Cria jogos de um torneio automaticamente fase de grupos e playoffs'''
        duplas = self.shuffle_teams()
        grupos = self.create_groups(duplas)
        jogos_criados = []
        if isinstance(grupos, Exception):
            return grupos

        if self.jogo_set.exists():
            self.jogo_set.all().delete()

        # Criar jogos de grupos
        for i, grupo in enumerate(grupos, 1):
            rodadas = self.organizar_jogos_por_rodadas(grupo)

            for jogos_rodada in rodadas:
                for dupla1, dupla2 in jogos_rodada:
                    jogo = Jogo(
                        torneio=self,
                        dupla1=dupla1,
                        dupla2=dupla2,
                        fase=f'GRUPO {i}',
                    )
                    jogos_criados.append(jogo)

        # Próximas fases
        if self.playoffs:
            n_grupos = self.quantidade_grupos
            template = GROUPS_TEMPLATES.get(n_grupos)

            if template:
                for fase, jogos in template.items():
                    if fase == 'TERCEIRO LUGAR' and not self.terceiro_lugar:
                        continue

                    for jogo_info in jogos:
                        jogo = Jogo(
                            torneio=self,
                            dupla1=None,
                            dupla2=None,
                            fase=fase,
                            playoff_number=jogo_info.get('jogo'),
                            playoff_help_text=f'{jogo_info.get("dupla1") or "BYE"}x{jogo_info.get("dupla2") or "BYE"}'
                        )
                        jogos_criados.append(jogo)

        Jogo.objects.bulk_create(jogos_criados)
        return jogos_criados

    def process_groups(self) -> list:
        '''Automatiza a classificação e distribuição dos times para a próximas fase'''
        classificados = []
        ranking = self.get_groups_ranking()
        for duplas in ranking.values():
            classificados += duplas[0:2]
        return classificados

    def _resolve_team_code(self, code: str, ranking: dict) -> Dupla | None:
        if not code:
            return None
        
        # Formato '1 G1'
        if 'º G' in code:
            pos_str, grupo_num = code.split('º G')
            try:
                pos = int(pos_str)
                grupo_nome = f'GRUPO {grupo_num}'
                if grupo_nome in ranking:
                    grupo_ranking = ranking[grupo_nome]
                    jogos_grupo = self.jogo_set.filter(torneio=self, fase=grupo_nome)
                    if jogos_grupo.exists() and jogos_grupo.filter(concluido='P').count() == 0:
                        for team_stat in grupo_ranking:
                            if team_stat['posicao'] == pos:
                                return team_stat['dupla']
            except (ValueError, IndexError):
                pass
        
        # Formato 'W 1' ou 'L 2'
        elif code.startswith('W ') or code.startswith('L '):
            parts = code.split(' ')
            if len(parts) == 2:
                condition = parts[0]
                try:
                    num_jogo = int(parts[1])
                    jogo = self.jogo_set.filter(torneio=self, playoff_number=num_jogo).first()
                    if jogo and jogo.concluido == 'C':
                        if condition == 'W':
                            return jogo.vencedor
                        elif condition == 'L':
                            if jogo.vencedor == jogo.dupla1:
                                return jogo.dupla2
                            elif jogo.vencedor == jogo.dupla2:
                                return jogo.dupla1
                except ValueError:
                    pass

        return None

    def next_stage(self) -> bool | Exception:
        '''Automatiza a classificação e preenchimento de todas as fases, do grupo para a final.'''
        if not self.playoffs:
            return Exception('Torneio não possui playoffs.')
            
        n_grupos = self.quantidade_grupos
        template = GROUPS_TEMPLATES.get(n_grupos)
        ranking = self.get_groups_ranking()
        
        if not template:
            if n_grupos == 1:
                # Caso de apenas 1 grupo (final direta)
                grupo1_ranking = ranking.get('GRUPO 1', [])
                jogos_grupo = self.jogo_set.filter(torneio=self, fase='GRUPO 1')
                if jogos_grupo.exists() and jogos_grupo.filter(concluido='P').count() == 0:
                    final = self.jogo_set.filter(torneio=self, fase='FINAL').first()
                    if final and final.concluido == 'P':
                        if final.dupla1 is None:
                            final.dupla1 = grupo1_ranking[0]['dupla'] if len(grupo1_ranking) > 0 else None
                        if final.dupla2 is None:
                            final.dupla2 = grupo1_ranking[1]['dupla'] if len(grupo1_ranking) > 1 else None
                        final.save()
            return True

        for fase, jogos in template.items():
            if fase == 'TERCEIRO LUGAR' and not self.terceiro_lugar:
                continue
                
            jogos_template = jogos
            
            for jogo_info in jogos_template:
                num_jogo = jogo_info.get('jogo')
                code_dupla1 = jogo_info.get('dupla1')
                code_dupla2 = jogo_info.get('dupla2')
                
                jogo = self.jogo_set.filter(torneio=self, fase=fase, playoff_number=num_jogo).first()
                if jogo and jogo.concluido == 'P':
                    # Resolve dupla 1
                    if jogo.dupla1 is None and code_dupla1 is not None:
                        jogo.dupla1 = self._resolve_team_code(code_dupla1, ranking)
                    
                    # Resolve dupla 2
                    if jogo.dupla2 is None and code_dupla2 is not None:
                        jogo.dupla2 = self._resolve_team_code(code_dupla2, ranking)
                    
                    jogo.save()
                    
                    # Trata o BYE (quando no template a oposição é explicitamente None)
                    if jogo.dupla1 is not None and code_dupla2 is None:
                        jogo.pontos_dupla1 = 1
                        jogo.pontos_dupla2 = 0
                        jogo.save()
                    elif jogo.dupla2 is not None and code_dupla1 is None:
                        jogo.pontos_dupla1 = 0
                        jogo.pontos_dupla2 = 1
                        jogo.save()

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

    def get_groups_ranking(self) -> dict:
        '''Retorna a classificação de todas as duplas, organizadas por grupo, ordenadas por vitórias e pontos.'''
        classificacao = {}
        jogos = self.jogo_set.filter(torneio=self, fase__startswith='GRUPO')

        # Separar jogos por grupo
        grupos = {}
        for jogo in jogos:
            grupo = jogo.fase  # Ex: 'GRUPO 1', 'GRUPO 2', ...
            if grupo not in grupos:
                grupos[grupo] = []
            grupos[grupo].append(jogo)

        # Processar cada grupo
        for grupo, jogos_do_grupo in grupos.items():
            estatisticas = {}

            # Coletar estatísticas de cada dupla
            for jogo in jogos_do_grupo:
                if jogo.dupla1 not in estatisticas:
                    estatisticas[jogo.dupla1] = {
                        'vitorias': 0,
                        'pontos': 0,
                        'saldo': 0,
                        'dupla': jogo.dupla1,
                        'jogos': 0
                    }
                if jogo.dupla2 not in estatisticas:
                    estatisticas[jogo.dupla2] = {
                        'vitorias': 0,
                        'pontos': 0,
                        'saldo': 0,
                        'dupla': jogo.dupla2,
                        'jogos': 0
                    }

                if jogo.concluido == 'C':
                    # Atualiza vitórias e pontos
                    if jogo.pontos_dupla1 > jogo.pontos_dupla2:
                        estatisticas[jogo.dupla1]['vitorias'] += 1
                    elif jogo.pontos_dupla1 < jogo.pontos_dupla2:
                        estatisticas[jogo.dupla2]['vitorias'] += 1

                    estatisticas[jogo.dupla1]['pontos'] += jogo.pontos_dupla1
                    estatisticas[jogo.dupla1]['saldo'] += jogo.pontos_dupla1
                    estatisticas[jogo.dupla1]['saldo'] -= jogo.pontos_dupla2
                    estatisticas[jogo.dupla1]['jogos'] += 1

                    estatisticas[jogo.dupla2]['pontos'] += jogo.pontos_dupla2
                    estatisticas[jogo.dupla2]['saldo'] += jogo.pontos_dupla2
                    estatisticas[jogo.dupla2]['saldo'] -= jogo.pontos_dupla1
                    estatisticas[jogo.dupla2]['jogos'] += 1

            # Ordenar as duplas por vitórias, saldo e pontos
            items = estatisticas.values()
            ranking = sorted(items, key=lambda x: (-x['vitorias'], -x['saldo'], -x['pontos']))
            ranking_result = []
            j_0 = {'pontos': 0, 'saldo': 0, 'vitorias': 0, 'posicao': 1}
            for i, j_1 in enumerate(ranking):
                if (j_1['pontos'] == j_0['pontos']) and (j_1['saldo'] == j_0['saldo']) and (j_1['vitorias'] == j_0['vitorias']):
                    j_1['posicao'] = j_0['posicao']
                else:
                    j_1['posicao'] = i + 1
                    j_0 = j_1
                ranking_result.append(j_1)

            # Salvar classificação no dicionário
            classificacao[grupo] = ranking_result

        return classificacao

    def organizar_jogos_por_rodadas(self, grupo) -> list:
        '''Organiza jogos de um grupo em rodadas para equilibrar o descanso das duplas'''
        n_duplas = len(grupo)
        if n_duplas < 2:
            return []
        rodadas = []
        if n_duplas % 2 == 0:
            rodadas = self.round_robin_par(grupo)
        else:
            rodadas = self.round_robin_impar(grupo)
        return rodadas

    def round_robin_par(self, duplas) -> list:
        '''Algoritmo Round Robin para número par de duplas'''
        n = len(duplas)
        rodadas = []

        # Fixa a primeira dupla e rotaciona as outras
        duplas_rotacao = duplas[1:]  # Remove a primeira dupla

        for rodada in range(n - 1):
            jogos_rodada = []

            # Primeiro jogo: primeira dupla vs a dupla atual da rotação
            jogos_rodada.append((duplas[0], duplas_rotacao[0]))

            # Outros jogos: emparelha as duplas restantes
            for i in range(1, n // 2):
                dupla1 = duplas_rotacao[i]
                dupla2 = duplas_rotacao[n - 1 - i]
                jogos_rodada.append((dupla1, dupla2))

            rodadas.append(jogos_rodada)

            # Rotaciona as duplas (menos a primeira que fica fixa)
            duplas_rotacao = [duplas_rotacao[-1]] + duplas_rotacao[:-1]

        return rodadas

    def round_robin_impar(self, duplas) -> list:
        '''Algoritmo Round Robin para número ímpar de duplas (com bye)'''
        # Adiciona uma dupla "fantasma" para tornar o número par
        duplas_com_bye = duplas + [None]  # None representa o "bye"
        n = len(duplas_com_bye)
        rodadas = []

        duplas_rotacao = duplas_com_bye[1:]  # Remove a primeira dupla

        for rodada in range(n - 1):
            jogos_rodada = []

            # Primeiro "jogo": primeira dupla vs a dupla atual da rotação
            oponente = duplas_rotacao[0]
            if oponente is not None:  # Se não é bye
                jogos_rodada.append((duplas_com_bye[0], oponente))

            # Outros jogos: emparelha as duplas restantes
            for i in range(1, n // 2):
                dupla1 = duplas_rotacao[i]
                dupla2 = duplas_rotacao[n - 1 - i]

                # Só adiciona se nenhuma das duplas é None (bye)
                if dupla1 is not None and dupla2 is not None:
                    jogos_rodada.append((dupla1, dupla2))

            if jogos_rodada:  # Só adiciona rodadas que tenham jogos
                rodadas.append(jogos_rodada)

            # Rotaciona as duplas (menos a primeira que fica fixa)
            duplas_rotacao = [duplas_rotacao[-1]] + duplas_rotacao[:-1]

        return rodadas

    def team_title(self, number='') -> str:
        '''Retorna o cabeçalho de dupla ou jogador'''
        TIPO = {
            'S': 'Jogador',
            'D': 'Dupla',
        }
        return f'{TIPO[self.tipo]} {number}'

    def get_sorted_games(self, queryset):
        '''Organiza os jogos em ordem de grupos e fases'''
        if self.quantidade_grupos > 1:
            jogos_grupos = queryset.filter(fase__startswith='GRUPO').values_list('id', 'fase')
            grupos = {
                'GRUPO 1': [], 
                'GRUPO 2': [], 
                'GRUPO 3': [], 
                'GRUPO 4': [],
                'GRUPO 5': [],
                'GRUPO 6': [],
                'GRUPO 7': [],
                'GRUPO 8': [],
            }
            for jogo_id, fase in jogos_grupos:
                if fase in grupos:
                    grupos[fase].append(jogo_id)

            alternada = []
            for elementos in zip_longest(*grupos.values(), fillvalue=None):
                alternada.extend([id_jogo for id_jogo in elementos if id_jogo is not None])

            ids_playoff = list(queryset.exclude(fase__startswith='GRUPO').annotate(
                fase_order=models.Case(
                    models.When(fase='OITAVAS', then=0),
                    models.When(fase='QUARTAS', then=1),
                    models.When(fase='SEMIFINAIS', then=2),
                    models.When(fase='TERCEIRO LUGAR', then=3),
                    models.When(fase='FINAL', then=4),
                    models.When(fase='CAMPEAO', then=5),
                    default=99,
                    output_field=models.IntegerField()
                )
            ).order_by('fase_order', 'id').values_list('id', flat=True))
            alternada.extend(ids_playoff)

            return queryset.filter(id__in=alternada).annotate(
                custom_order=models.Case(
                    *[models.When(id=id_val, then=pos) for pos, id_val in enumerate(alternada)],
                    output_field=models.IntegerField()
                )
            ).order_by('custom_order')

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
        if not 'G' in help_text:
            return None

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


class Ranking(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_por = models.ForeignKey('auth.User', related_name='rankings_criados', on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
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
