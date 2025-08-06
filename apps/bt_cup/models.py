import random
from django.db import models
from django.utils.html import format_html
from shortuuid.django_fields import ShortUUIDField


FASE_CHOICES = [
    ('GRUPO 1', 'GRUPO 1'),
    ('GRUPO 2', 'GRUPO 2'),
    ('GRUPO 3', 'GRUPO 3'),
    ('GRUPO 4', 'GRUPO 4'),
    ('OITAVAS', 'OITAVAS'),
    ('QUARTAS', 'QUARTAS'),
    ('SEMIFINAIS', 'SEMI-FINAIS'),
    ('FINAL', 'FINAL'),
    ('CAMPEAO', 'CAMPEÃO'),
]


QUANTIDADE_GRUPOS_CHOICES = [
    (1, '1'),
    (2, '2'),
    (4, '4'),
    (8, '8')
]


class Dupla(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    jogador1 = models.CharField(max_length=100, verbose_name='Jogador 1')
    jogador2 = models.CharField(max_length=100, verbose_name='Jogador 2')
    telefone = models.CharField(max_length=20, blank=True, null=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Dupla'
        verbose_name_plural = 'Duplas'
        ordering = ['jogador1', 'jogador2']

    def __str__(self):
        return f'{self.jogador1}/{self.jogador2}'

    def render(self):
        return format_html('{}<br/>{}', self.jogador1, self.jogador2)

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

        # Inicializar estatísticas para todas as duplas no grupo
        estatisticas = {}

        # Processar jogos do grupo para calcular vitórias e pontos
        for jogo in jogos_grupo:
            if jogo.placar_dupla1 is not None and jogo.placar_dupla2 is not None:
                estatisticas[jogo.dupla1] = estatisticas.get(jogo.dupla1, {'vitorias': 0, 'pontos': 0, 'grupo': int(grupo[6:])})
                estatisticas[jogo.dupla2] = estatisticas.get(jogo.dupla2, {'vitorias': 0, 'pontos': 0, 'grupo': int(grupo[6:])})

                if jogo.placar_dupla1 > jogo.placar_dupla2:
                    estatisticas[jogo.dupla1]['vitorias'] += 1
                elif jogo.placar_dupla2 > jogo.placar_dupla1:
                    estatisticas[jogo.dupla2]['vitorias'] += 1

                estatisticas[jogo.dupla1]['pontos'] += jogo.placar_dupla1
                estatisticas[jogo.dupla2]['pontos'] += jogo.placar_dupla2

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
    duplas = models.ManyToManyField(Dupla, blank=True)
    quantidade_grupos = models.IntegerField(
        choices=QUANTIDADE_GRUPOS_CHOICES,
        default=2,
        verbose_name='Nº grupos',
        help_text=format_html('''
            Selecione o número de grupos para distribuir as duplas
            <ul>
                <li>1 grupo: Fase de grupo e FINAL</li>
                <li>2 grupos: Fase de grupo, SEMIFINAIS e FINAL</li>
                <li>4 grupos: Fase de grupo, QUARTAS, SEMIFINAIS e FINAL</li>
                <li>8 grupos: Fase de grupo, OITAVAS, QUARTAS, SEMIFINAIS e FINAL</li>
            </ul>
        ''')
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', related_name='torneios_criados', on_delete=models.SET_NULL, null=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Torneio'
        verbose_name_plural = 'Torneios'
        ordering = ['-data']

    def __str__(self):
        return self.nome

    def create_groups(self, duplas):
        '''Distribui duplas em grupos de forma aleatória'''
        if len(duplas) < self.quantidade_grupos:
            return Exception(f'Número de duplas {len(duplas)} menor que número de grupos {self.quantidade_grupos}')

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

    def create_games(self):
        '''Cria jogos de um torneio automaticamente, com todos jogando contra todos no grupo'''
        if self.jogo_set.exists():
            self.jogo_set.all().delete()

        duplas = list(self.duplas.all())

        random.shuffle(duplas)
        grupos = self.create_groups(duplas)
        if isinstance(grupos, Exception):
            return grupos

        jogos_criados = {
            'grupos': {},
            'oitavas': [],
            'quartas': [],
            'semifinais': [],
            'final': None
        }

        # Criar jogos de grupos
        for i, grupo in enumerate(grupos, 1):
            rodadas = self.organizar_jogos_por_rodadas(grupo)
            grupo_jogos = []

            for num_rodada, jogos_rodada in enumerate(rodadas, 1):
                for dupla1, dupla2 in jogos_rodada:
                    jogo = Jogo.objects.create(
                        torneio=self,
                        dupla1=dupla1,
                        dupla2=dupla2,
                        fase=f'GRUPO {i}',
                    )
                    grupo_jogos.append(jogo)

            jogos_criados['grupos'][f'grupo {i}'] = grupo_jogos

        # Preparar próximas fases
        n_grupos = self.quantidade_grupos
        if n_grupos == 8:
            for i in range(8): # Oitavas de final
                oitava = Jogo.objects.create(
                    torneio=self,
                    dupla1=None,  # Será preenchido após grupos
                    dupla2=None,  # Será preenchido após grupos
                    fase='OITAVAS'
                )
                jogos_criados['oitavas'].append(oitava)

        if n_grupos >= 4:
            for i in range(4): # Quartas de final
                quarta = Jogo.objects.create(
                    torneio=self,
                    dupla1=None,  # Será preenchido após oitavas
                    dupla2=None,  # Será preenchido após oitavas
                    fase='QUARTAS'
                )
                jogos_criados['quartas'].append(quarta)

        if n_grupos >= 2:
            for i in range(2): # Semifinais
                semi = Jogo.objects.create(
                    torneio=self,
                    dupla1=None,  # Será preenchido após oitavas
                    dupla2=None,  # Será preenchido após oitavas
                    fase='SEMIFINAIS'
                )
                jogos_criados['semifinais'].append(semi)

        # Final sempre será criado
        final = Jogo.objects.create(
            torneio=self,
            dupla1=None,
            dupla2=None,
            fase='FINAL'
        )
        jogos_criados['final'] = final

        return jogos_criados

    def process_groups(self):
        '''Automatiza a classificação e distribuição dos times para a próximas fase'''
        jogos_por_fase = {
            'GRUPO': [],
            'OITAVAS': [],
            'QUARTAS': [],
            'SEMIFINAIS': [],
            'FINAL': []
        }

        # Recuperar todos os jogos do torneio
        jogos = Jogo.objects.filter(torneio=self)

        # 1. Identificar os jogos de grupos
        for i in range(1, self.quantidade_grupos + 1):  # GRUPO 1, GRUPO 2, ..., GRUPO N
            grupo_jogos = jogos.filter(fase=f'GRUPO {i}')
            if grupo_jogos:
                jogos_por_fase['GRUPO'].append(grupo_jogos)

        # 2. Selecionar os dois melhores de cada grupo
        classificados = []
        for grupo_jogos in jogos_por_fase['GRUPO']:
            # Cria um ranking baseado no número de vitórias e pontuação
            estatisticas = {}
            for jogo in grupo_jogos:
                if jogo.concluido:
                    # Atualiza estatísticas para dupla 1
                    if jogo.dupla1 not in estatisticas:
                        estatisticas[jogo.dupla1] = {'vitorias': 0, 'pontos': 0}
                    if jogo.dupla2 not in estatisticas:
                        estatisticas[jogo.dupla2] = {'vitorias': 0, 'pontos': 0}

                    # Vitória de dupla 1
                    if jogo.placar_dupla1 > jogo.placar_dupla2:
                        estatisticas[jogo.dupla1]['vitorias'] += 1
                    elif jogo.placar_dupla1 < jogo.placar_dupla2:
                        estatisticas[jogo.dupla2]['vitorias'] += 1
                    estatisticas[jogo.dupla1]['pontos'] += jogo.placar_dupla1
                    estatisticas[jogo.dupla2]['pontos'] += jogo.placar_dupla2

            # Ordena as duplas primeiro por vitórias e depois por pontuação
            classificados_grupo = sorted(
                estatisticas.keys(),
                key=lambda dupla: (estatisticas[dupla]['vitorias'], estatisticas[dupla]['pontos']),
                reverse=True
            )[:2]  # Seleciona os dois melhores
            classificados.extend(classificados_grupo)
        return classificados

    def next_stage(self):
        '''Automatiza a passagem dos vencedores das fases (Oitavas -> Quartas -> Semifinais -> Final)'''
        # Lista de fases e sua ordem
        fases = ['OITAVAS', 'QUARTAS', 'SEMIFINAIS', 'FINAL']

        for i, fase in enumerate(fases):
            # Buscar os jogos da fase atual
            jogos_atuais = Jogo.objects.filter(torneio=self, fase=fase, concluido=True)

            # Verificar se todos os jogos da fase atual foram concluídos
            if len(jogos_atuais) == 0: # Nenhum jogo concluído, ignorar a fase
                continue
            elif jogos_atuais.count() != Jogo.objects.filter(torneio=self, fase=fase).count(): # jogos pendentes
                return Exception(f'Aguardando conclusão de todos os jogos da fase {fase}.')

            # Checar se existe uma próxima fase
            if i + 1 >= len(fases):
                # Não há próxima fase
                continue

            proxima_fase = fases[i + 1]

            # Buscar os jogos da próxima fase
            jogos_proxima_fase = Jogo.objects.filter(torneio=self, fase=proxima_fase)

            # Garantir que os jogos da próxima fase foram criados, mas ainda não preenchidos
            if not jogos_proxima_fase.exists():
                return Exception(f'Jogos da próxima fase ({proxima_fase}) ainda não foram criados.')

            jogos_proxima_fase = list(jogos_proxima_fase)

            # Preencher os vencedores nos jogos da próxima fase
            vencedores = []
            for jogo in jogos_atuais:
                # Adiciona o vencedor do jogo (se os placares estão definidos)
                if jogo.placar_dupla1 > jogo.placar_dupla2:
                    vencedores.append(jogo.dupla1)
                elif jogo.placar_dupla2 > jogo.placar_dupla1:
                    vencedores.append(jogo.dupla2)

            # Preencher os vencedores na próxima fase
            if len(vencedores) != len(jogos_proxima_fase) * 2:
                return Exception(f'Erro: O número de vencedores ({len(vencedores)}) não corresponde ao esperado para a fase {proxima_fase}.')

            for index, jogo in enumerate(jogos_proxima_fase):
                if jogo.dupla1 is None:
                    jogo.dupla1 = vencedores.pop(0)
                if jogo.dupla2 is None:
                    jogo.dupla2 = vencedores.pop(0)
                jogo.save()

        return True

    def finish(self):
        # self.duplas.all().update(ativo=False)
        self.ativo = False
        self.save()

    def is_finished(self):
        return Jogo.objects.filter(torneio=self, fase='FINAL', concluido=True).exists()

    def has_games(self):
        return Jogo.objects.filter(torneio=self).exists()

    def get_groups_ranking(self):
        '''Retorna a classificação de todas as duplas, organizadas por grupo, ordenadas por vitórias e pontos.'''
        # Dicionário para armazenar as classificações por grupo
        classificacao = {}

        # Recuperar todos os jogos do torneio
        jogos = Jogo.objects.filter(torneio=self, fase__startswith='GRUPO')

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
                        'dupla': jogo.dupla1
                    }
                if jogo.dupla2 not in estatisticas:
                    estatisticas[jogo.dupla2] = {
                        'vitorias': 0,
                        'pontos': 0,
                        'saldo': 0,
                        'dupla': jogo.dupla2
                    }

                if jogo.concluido:
                    # Atualiza vitórias e pontos
                    if jogo.placar_dupla1 > jogo.placar_dupla2:
                        estatisticas[jogo.dupla1]['vitorias'] += 1
                    elif jogo.placar_dupla1 < jogo.placar_dupla2:
                        estatisticas[jogo.dupla2]['vitorias'] += 1

                    estatisticas[jogo.dupla1]['pontos'] += jogo.placar_dupla1
                    estatisticas[jogo.dupla1]['saldo'] += jogo.placar_dupla1
                    estatisticas[jogo.dupla1]['saldo'] -= jogo.placar_dupla2

                    estatisticas[jogo.dupla2]['pontos'] += jogo.placar_dupla2
                    estatisticas[jogo.dupla2]['saldo'] += jogo.placar_dupla2
                    estatisticas[jogo.dupla2]['saldo'] -= jogo.placar_dupla1

            # Ordenar as duplas por vitórias e pontos
            items = estatisticas.values()
            ranking = sorted(items, key=lambda x: (-x['vitorias'], -x['pontos'], -x['saldo']))
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

    def organizar_jogos_por_rodadas(self, grupo):
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

    def round_robin_par(self, duplas):
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

    def round_robin_impar(self, duplas):
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

class Jogo(models.Model):
    torneio = models.ForeignKey(Torneio, on_delete=models.CASCADE)
    dupla1 = models.ForeignKey(Dupla, related_name='dupla1', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Dupla 1')
    dupla2 = models.ForeignKey(Dupla, related_name='dupla2', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Dupla 2')
    placar_dupla1 = models.IntegerField(null=True, blank=True, verbose_name='')
    placar_dupla2 = models.IntegerField(null=True, blank=True, verbose_name='')
    fase = models.CharField(max_length=100, null=True, blank=True)
    concluido = models.BooleanField(default=False, verbose_name='')
    obs = models.TextField(null=True, blank=True, help_text='Alguma observação sobre o jogo. Ex: "Dupla 1 WO"')

    def __str__(self):
        return f'{self.dupla1} X {self.dupla2}'

    def save(self, *args, **kwargs):
        if self.dupla1 is None and self.dupla2 is None:
            self.placar_dupla1 = None
            self.placar_dupla2 = None

        self.concluido = (
            self.placar_dupla1 is not None and
            self.placar_dupla1 != '' and
            self.placar_dupla2 is not None and
            self.placar_dupla2 != ''
        )
        super().save(*args, **kwargs)

    @property
    def winner(self):
        if self.placar_dupla1 is not None and self.placar_dupla2 is not None:
            if self.placar_dupla1 > self.placar_dupla2:
                return self.dupla1
            elif self.placar_dupla2 > self.placar_dupla1:
                return self.dupla2
        return None
