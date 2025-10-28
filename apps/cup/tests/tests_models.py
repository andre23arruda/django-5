import random
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from ..models import Jogador, Dupla, Torneio, Jogo, Ranking


class JogadorModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_jogador_creation(self):
        '''Testa a criação básica de um jogador'''
        jogador = Jogador.objects.create(
            nome='João Silva',
            telefone='11999999999',
            criado_por=self.user
        )

        self.assertEqual(jogador.nome, 'João Silva')
        self.assertEqual(jogador.telefone, '11999999999')
        self.assertEqual(jogador.jogos, 0)
        self.assertEqual(jogador.vitorias, 0)
        self.assertEqual(jogador.derrotas, 0)
        self.assertTrue(jogador.ativo)
        self.assertEqual(jogador.criado_por, self.user)
        self.assertIsNotNone(jogador.id)

    def test_jogador_str_method(self):
        '''Testa o método __str__ do jogador'''
        jogador = Jogador.objects.create(nome='Maria Santos')
        self.assertEqual(str(jogador), 'Maria Santos')

    def test_jogador_ordering(self):
        '''Testa se a ordenação por nome funciona'''
        Jogador.objects.create(nome='Zé')
        Jogador.objects.create(nome='Ana')
        Jogador.objects.create(nome='Bruno')

        jogadores = list(Jogador.objects.all())
        self.assertEqual(jogadores[0].nome, 'Ana')
        self.assertEqual(jogadores[1].nome, 'Bruno')
        self.assertEqual(jogadores[2].nome, 'Zé')

    def test_jogador_without_phone(self):
        '''Testa criação de jogador sem telefone'''
        jogador = Jogador.objects.create(nome='Sem Telefone')
        self.assertIsNone(jogador.telefone)


class DuplaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.torneio = Torneio.objects.create(
            nome='Teste Torneio',
            data=date.today(),
            criado_por=self.user
        )

        self.jogador1 = Jogador.objects.create(nome='João')
        self.jogador2 = Jogador.objects.create(nome='Maria')
        self.jogador3 = Jogador.objects.create(nome='Pedro')

    def test_dupla_creation_with_two_players(self):
        '''Testa criação de dupla com dois jogadores'''
        dupla = Dupla.objects.create(
            jogador1=self.jogador1,
            jogador2=self.jogador2,
            torneio=self.torneio,
            criado_por=self.user
        )

        self.assertEqual(dupla.jogador1, self.jogador1)
        self.assertEqual(dupla.jogador2, self.jogador2)
        self.assertEqual(dupla.torneio, self.torneio)
        self.assertTrue(dupla.ativo)

    def test_dupla_creation_with_one_player(self):
        '''Testa criação de dupla com apenas um jogador'''
        dupla = Dupla.objects.create(
            jogador1=self.jogador1,
            torneio=self.torneio,
            criado_por=self.user
        )

        self.assertEqual(dupla.jogador1, self.jogador1)
        self.assertIsNone(dupla.jogador2)

    def test_dupla_str_method_two_players(self):
        '''Testa método __str__ com dois jogadores'''
        dupla = Dupla.objects.create(
            jogador1=self.jogador1,
            jogador2=self.jogador2,
            torneio=self.torneio
        )
        self.assertEqual(str(dupla), 'João/Maria')

    def test_dupla_str_method_one_player(self):
        '''Testa método __str__ com um jogador'''
        dupla = Dupla.objects.create(
            jogador1=self.jogador1,
            torneio=self.torneio
        )
        self.assertEqual(str(dupla), 'João')

    def test_dupla_render_method(self):
        '''Testa método render'''
        dupla = Dupla.objects.create(
            jogador1=self.jogador1,
            jogador2=self.jogador2,
            torneio=self.torneio
        )
        rendered = dupla.render()
        self.assertIn('João', rendered)
        self.assertIn('Maria', rendered)
        self.assertIn('<br/>', rendered)

    def test_dupla_render_special_method(self):
        '''Testa método render_special'''
        dupla = Dupla.objects.create(
            jogador1=self.jogador1,
            jogador2=self.jogador2,
            torneio=self.torneio
        )
        rendered = dupla.render_special()
        self.assertEqual(rendered, 'João\nMaria')

    def test_get_group_method(self):
        '''Testa método get_group'''
        dupla = Dupla.objects.create(
            jogador1=self.jogador1,
            jogador2=self.jogador2,
            torneio=self.torneio
        )

        # Cria jogo do grupo
        Jogo.objects.create(
            torneio=self.torneio,
            dupla1=dupla,
            dupla2=None,
            fase='GRUPO 1'
        )

        grupo = dupla.get_group(self.torneio)
        self.assertEqual(grupo, 'GRUPO 1')

    def test_get_group_data_method(self):
        '''Testa método get_group_data'''
        dupla1 = Dupla.objects.create(
            jogador1=self.jogador1,
            torneio=self.torneio
        )
        dupla2 = Dupla.objects.create(
            jogador1=self.jogador2,
            torneio=self.torneio
        )

        # Cria jogo com resultado
        Jogo.objects.create(
            torneio=self.torneio,
            dupla1=dupla1,
            dupla2=dupla2,
            fase='GRUPO 1',
            pontos_dupla1=10,
            pontos_dupla2=5,
            concluido='C'
        )

        grupo_neg, pos_neg, vitorias, pontos = dupla1.get_group_data(self.torneio)
        self.assertEqual(vitorias, 1)
        self.assertEqual(pontos, 10)


class TorneioModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.ranking = Ranking.objects.create(
            nome='Ranking Teste',
            criado_por=self.user
        )

    def test_torneio_creation(self):
        '''Testa criação básica de torneio'''
        torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date.today(),
            quantidade_grupos=2,
            criado_por=self.user,
            ranking=self.ranking
        )

        self.assertEqual(torneio.nome, 'Torneio Teste')
        self.assertEqual(torneio.quantidade_grupos, 2)
        self.assertTrue(torneio.ativo)
        self.assertTrue(torneio.playoffs)
        self.assertFalse(torneio.terceiro_lugar)
        self.assertFalse(torneio.open)
        self.assertEqual(torneio.tipo, 'D')
        self.assertEqual(torneio.ranking, self.ranking)

    def test_torneio_str_method(self):
        '''Testa método __str__'''
        torneio = Torneio.objects.create(
            nome='Torneio Legal',
            data=date.today()
        )
        self.assertEqual(str(torneio), 'Torneio Legal')

    def test_torneio_slug_creation(self):
        '''Testa criação automática do slug'''
        torneio = Torneio.objects.create(
            nome='Torneio com Espaços',
            data=date.today()
        )
        self.assertIn('torneio-com-espacos', torneio.slug)
        self.assertIn(torneio.id, torneio.slug)

    def test_shuffle_teams(self):
        '''Testa embaralhamento de duplas'''
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today()
        )

        # Cria duplas
        jogadores = [Jogador.objects.create(nome=f'Jogador {i}') for i in range(8)]
        for i in range(0, 8, 2):
            Dupla.objects.create(
                jogador1=jogadores[i],
                jogador2=jogadores[i+1],
                torneio=torneio)

        shuffled = torneio.shuffle_teams()
        self.assertEqual(len(shuffled), 4)
        # Com seed fixo, o resultado deve ser reproduzível
        shuffled2 = torneio.shuffle_teams()
        self.assertEqual(shuffled, shuffled2)

    def test_draw_pairs(self):
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today(),
            quantidade_grupos=1,
            draw_pairs=1,
        )
        # Cria 6 duplas
        jogadores = [Jogador.objects.create(nome=f'Jogador {i}') for i in range(12)]
        duplas = [
            Dupla.objects.create(jogador1=jogadores[i], jogador2=jogadores[i+1], torneio=torneio)
            for i in range(0, 12, 2)
        ]
        dupla_1 = torneio.duplas.first().__str__()
        torneio.shuffle_teams()
        dupla_1_new = torneio.duplas.first().__str__()
        self.assertNotEqual(dupla_1, dupla_1_new)

    def test_create_groups(self):
        '''Testa criação de grupos'''
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today(),
            quantidade_grupos=2
        )

        # Cria 6 duplas
        jogadores = [Jogador.objects.create(nome=f'Jogador {i}') for i in range(12)]
        duplas = [
            Dupla.objects.create(jogador1=jogadores[i], jogador2=jogadores[i+1], torneio=torneio)
            for i in range(0, 12, 2)
        ]

        grupos = torneio.create_groups(duplas)
        self.assertEqual(len(grupos), 2)
        # Verifica distribuição (3 duplas em cada grupo)
        self.assertEqual(len(grupos[0]), 3)
        self.assertEqual(len(grupos[1]), 3)

    def test_create_groups_with_fewer_teams_than_groups(self):
        '''Testa criação de grupos com duplas insuficientes'''
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today(),
            quantidade_grupos=4
        )

        # Apenas 2 duplas para 4 grupos
        jogadores = [Jogador.objects.create(nome=f'Jogador {i}') for i in range(2)]
        duplas = [
            Dupla.objects.create(jogador1=jogadores[i], torneio=torneio)
            for i in range(2)
        ]

        result = torneio.create_groups(duplas)
        error_msg = str(result)
        self.assertIsInstance(result, Exception)
        self.assertEqual('Número de duplas é menor que número de grupos', error_msg)

    def test_create_groups_with_insuficient_teams(self):
        '''Testa criação de grupos com duplas insuficientes'''
        torneio = Torneio.objects.create(
            nome='Teste 2',
            data=date.today(),
            quantidade_grupos=2
        )

        # Apenas 2 duplas para 4 grupos
        jogadores = [Jogador.objects.create(nome=f'Jogador {i}') for i in range(2)]
        duplas = [
            Dupla.objects.create(jogador1=jogadores[i], torneio=torneio)
            for i in range(2)
        ]

        result = torneio.create_groups(duplas)
        error_msg = str(result)
        self.assertIsInstance(result, Exception)
        self.assertEqual(f'Número de duplas insuficientes para {torneio.quantidade_grupos} grupos', error_msg)

    def test_create_games_basic(self):
        '''Testa criação básica de jogos'''
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today(),
            quantidade_grupos=1,
            playoffs=False
        )

        # Cria 4 duplas
        jogadores = [Jogador.objects.create(nome=f'Jogador {i}') for i in range(4)]
        duplas = [
            Dupla.objects.create(jogador1=jogadores[i], torneio=torneio)
            for i in range(4)
        ]

        jogos = torneio.create_games()
        self.assertIsInstance(jogos, list)
        # Com 4 duplas, deve ter 6 jogos (todos contra todos)
        self.assertEqual(len(jogos), 6)

    def test_create_games_with_playoffs(self):
        '''Testa criação de jogos com playoffs'''
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today(),
            quantidade_grupos=2,
            playoffs=True
        )

        # Cria 4 duplas
        jogadores = [Jogador.objects.create(nome=f'Jogador {i}') for i in range(4)]
        duplas = [
            Dupla.objects.create(jogador1=jogadores[i], torneio=torneio)
            for i in range(4)
        ]

        jogos = torneio.create_games()

        # Verifica se foram criados jogos de grupos + semifinais + final
        jogos_grupo = [j for j in jogos if j.fase.startswith('GRUPO')]
        jogos_semi = [j for j in jogos if j.fase == 'SEMIFINAIS']
        jogos_final = [j for j in jogos if j.fase == 'FINAL']

        self.assertEqual(len(jogos_grupo), 2)  # 1 jogo por grupo
        self.assertEqual(len(jogos_semi), 2)
        self.assertEqual(len(jogos_final), 1)

    def test_round_robin_par(self):
        '''Testa algoritmo round robin com número par'''
        torneio = Torneio.objects.create(nome='Teste', data=date.today())

        jogadores = [Jogador.objects.create(nome=f'J{i}') for i in range(4)]
        duplas = [Dupla.objects.create(jogador1=j, torneio=torneio) for j in jogadores]

        rodadas = torneio.round_robin_par(duplas)

        # Com 4 duplas, deve ter 3 rodadas
        self.assertEqual(len(rodadas), 3)
        # Cada rodada deve ter 2 jogos
        for rodada in rodadas:
            self.assertEqual(len(rodada), 2)

    def test_round_robin_impar(self):
        '''Testa algoritmo round robin com número ímpar'''
        torneio = Torneio.objects.create(nome='Teste', data=date.today())

        jogadores = [Jogador.objects.create(nome=f'J{i}') for i in range(3)]
        duplas = [Dupla.objects.create(jogador1=j, torneio=torneio) for j in jogadores]

        rodadas = torneio.round_robin_impar(duplas)

        # Com 3 duplas, deve ter 3 rodadas, algumas com 1 jogo (bye)
        self.assertEqual(len(rodadas), 3)

    def test_team_title_method(self):
        '''Testa método team_title'''
        torneio_simples = Torneio.objects.create(
            nome='Teste',
            data=date.today(),
            tipo='S'
        )
        torneio_duplas = Torneio.objects.create(
            nome='Teste',
            data=date.today(),
            tipo='D'
        )

        self.assertEqual(torneio_simples.team_title('1'), 'Jogador 1')
        self.assertEqual(torneio_duplas.team_title('2'), 'Dupla 2')

    def test_finish_method(self):
        '''Testa método finish'''
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today()
        )

        self.assertTrue(torneio.ativo)
        torneio.finish()
        self.assertFalse(torneio.ativo)

    def test_has_games_method(self):
        '''Testa método has_games'''
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today()
        )

        self.assertFalse(torneio.has_games())

        # Adiciona um jogo
        Jogo.objects.create(torneio=torneio, fase='GRUPO 1')
        self.assertTrue(torneio.has_games())

    def test_is_finished_method(self):
        '''Testa método is_finished'''
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today()
        )
        jogador1 = Jogador.objects.create(nome='João')
        jogador2 = Jogador.objects.create(nome='Maria')
        jogador3 = Jogador.objects.create(nome='Pedro')
        jogador4 = Jogador.objects.create(nome='Ana')

        dupla1 = Dupla.objects.create(
            jogador1=jogador1,
            jogador2=jogador2,
            torneio=torneio
        )
        dupla2 = Dupla.objects.create(
            jogador1=jogador3,
            jogador2=jogador4,
            torneio=torneio
        )

        # Sem jogos, considera finalizado
        self.assertTrue(torneio.is_finished())

        # Adiciona jogo não concluído
        Jogo.objects.create(
            torneio=torneio,
            dupla1=dupla1,
            dupla2=dupla2
        )
        self.assertFalse(torneio.is_finished())

        # Conclui o jogo
        jogo = torneio.jogo_set.first()
        jogo.concluido = 'C'
        jogo.pontos_dupla1 = 10
        jogo.pontos_dupla2 = 8
        jogo.save()
        self.assertTrue(torneio.is_finished())

    def test_create_games_deletes_existing(self):
        '''Testa que criar jogos deleta os jogos existentes'''
        torneio = Torneio.objects.create(
            nome='Teste',
            data=date.today()
        )

        # Cria duplas
        jogadores = [Jogador.objects.create(nome=f'Jogador {i}') for i in range(8)]
        for i in range(0, 8, 2):
            Dupla.objects.create(
                jogador1=jogadores[i],
                jogador2=jogadores[i+1],
                torneio=torneio)

        torneio.create_games()
        count_initial = Jogo.objects.filter(torneio=torneio).count()
        id_jogo_1 = Jogo.objects.filter(torneio=torneio).first().id

        torneio.create_games()
        count_after = Jogo.objects.filter(torneio=torneio).count()
        id_jogo_2 = Jogo.objects.filter(torneio=torneio).first().id

        self.assertEqual(count_initial, count_after)
        self.assertNotEqual(id_jogo_1, id_jogo_2)


class JogoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.torneio = Torneio.objects.create(
            nome='Teste Torneio',
            data=date.today(),
            criado_por=self.user
        )

        jogador1 = Jogador.objects.create(nome='João')
        jogador2 = Jogador.objects.create(nome='Maria')
        jogador3 = Jogador.objects.create(nome='Pedro')
        jogador4 = Jogador.objects.create(nome='Ana')

        self.dupla1 = Dupla.objects.create(
            jogador1=jogador1,
            jogador2=jogador2,
            torneio=self.torneio
        )
        self.dupla2 = Dupla.objects.create(
            jogador1=jogador3,
            jogador2=jogador4,
            torneio=self.torneio
        )

    def test_jogo_creation(self):
        '''Testa criação básica de jogo'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.dupla1,
            dupla2=self.dupla2,
            fase='GRUPO 1'
        )

        self.assertEqual(jogo.torneio, self.torneio)
        self.assertEqual(jogo.dupla1, self.dupla1)
        self.assertEqual(jogo.dupla2, self.dupla2)
        self.assertEqual(jogo.fase, 'GRUPO 1')
        self.assertEqual(jogo.concluido, 'P')
        self.assertIsNone(jogo.vencedor)

    def test_jogo_str_method(self):
        '''Testa método __str__'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.dupla1,
            dupla2=self.dupla2
        )
        self.assertEqual(str(jogo), 'João/Maria X Pedro/Ana')

    def test_jogo_str_method_undefined(self):
        '''Testa método __str__ com duplas indefinidas'''
        jogo = Jogo.objects.create(torneio=self.torneio)
        self.assertEqual(str(jogo), 'A definir')

    def test_placar_method(self):
        '''Testa método placar'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.dupla1,
            dupla2=self.dupla2
        )

        # Sem pontos
        self.assertEqual(jogo.placar(), '')

        # Com pontos
        jogo.pontos_dupla1 = 10
        jogo.pontos_dupla2 = 8
        self.assertEqual(jogo.placar(), '10 X 8')

    def test_jogo_save_with_score(self):
        '''Testa salvamento com placar definido'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.dupla1,
            dupla2=self.dupla2,
            pontos_dupla1=15,
            pontos_dupla2=10
        )

        self.assertEqual(jogo.concluido, 'C')
        self.assertEqual(jogo.vencedor, self.dupla1)

    def test_jogo_save_tie(self):
        '''Testa salvamento com empate'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.dupla1,
            dupla2=self.dupla2,
            pontos_dupla1=10,
            pontos_dupla2=10
        )

        self.assertEqual(jogo.concluido, 'C')
        self.assertIsNone(jogo.vencedor)

    def test_jogo_save_in_progress(self):
        '''Testa salvamento de jogo em andamento'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.dupla1,
            dupla2=self.dupla2,
            concluido='A'
        )

        self.assertEqual(jogo.concluido, 'A')

    def test_winner_property(self):
        '''Testa propriedade winner'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.dupla1,
            dupla2=self.dupla2
        )

        # Sem pontos
        self.assertIsNone(jogo.winner)

        # Com pontos
        jogo.pontos_dupla1 = 12
        jogo.pontos_dupla2 = 8
        self.assertEqual(jogo.winner, self.dupla1)

        jogo.pontos_dupla1 = 5
        jogo.pontos_dupla2 = 15
        self.assertEqual(jogo.winner, self.dupla2)


class RankingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_ranking_creation(self):
        '''Testa criação básica de ranking'''
        ranking = Ranking.objects.create(
            nome='Ranking Regional',
            criado_por=self.user
        )

        self.assertEqual(ranking.nome, 'Ranking Regional')
        self.assertTrue(ranking.ativo)
        self.assertEqual(ranking.criado_por, self.user)
        self.assertIsNotNone(ranking.id)

    def test_ranking_str_method(self):
        '''Testa método __str__'''
        ranking = Ranking.objects.create(nome='Ranking Estadual')
        self.assertEqual(str(ranking), 'Ranking Estadual')

    def test_ranking_ordering(self):
        '''Testa ordenação por nome'''
        ranking1 = Ranking.objects.create(nome='Ranking Z')
        ranking2 = Ranking.objects.create(nome='Ranking A')
        ranking3 = Ranking.objects.create(nome='Ranking M')

        rankings = list(Ranking.objects.all())
        self.assertEqual(rankings[0].nome, 'Ranking A')
        self.assertEqual(rankings[1].nome, 'Ranking M')
        self.assertEqual(rankings[2].nome, 'Ranking Z')


class IntegrationTest(TestCase):
    '''Testes de integração entre models'''

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.ranking = Ranking.objects.create(
            nome='Ranking Teste',
            criado_por=self.user
        )

    def test_complete_tournament_flow(self):
        '''Testa fluxo completo de um torneio'''
        # Cria torneio
        torneio = Torneio.objects.create(
            nome='Torneio Integração',
            data=date.today(),
            quantidade_grupos=2,
            playoffs=True,
            ranking=self.ranking,
            criado_por=self.user
        )

        # Cria 12 jogadores
        jogadores = []
        for i in range(12):
            jogador = Jogador.objects.create(
                nome=f'Jogador {i+1}',
                telefone=f'1199999999{i}',
                criado_por=self.user
            )
            jogadores.append(jogador)

        # Cria 4 duplas
        duplas = []
        for i in range(0, 12, 2):
            dupla = Dupla.objects.create(
                jogador1=jogadores[i],
                jogador2=jogadores[i+1] if i+1 < len(jogadores) else None,
                torneio=torneio,
                criado_por=self.user
            )
            duplas.append(dupla)

        # Cria jogos
        jogos_criados = torneio.create_games()
        self.assertGreater(len(jogos_criados), 0)

        # Verifica se todos os jogos foram salvos no banco
        jogos_db = torneio.jogo_set.all()
        self.assertEqual(len(jogos_criados), jogos_db.count())

        # Simula alguns resultados
        jogos_grupo = jogos_db.filter(fase__startswith='GRUPO')
        for jogo in jogos_grupo:
            jogo.pontos_dupla1 = random.randint(5, 15)
            jogo.pontos_dupla2 = random.randint(5, 15)
            jogo.save()

        # Verifica classificação dos grupos
        ranking_grupos = torneio.get_groups_ranking()
        ranking_grupo1 = ranking_grupos['GRUPO 1']
        ranking_grupo2 = ranking_grupos['GRUPO 2']
        self.assertEqual(len(ranking_grupo1), 3)  # 3 duplas no grupo 1
        self.assertEqual(len(ranking_grupo2), 3)  # 3 duplas no grupo 2

        # Verifica se tem duplas classificadas
        classificados = torneio.process_groups()
        self.assertEqual(len(classificados), 4)  # 2 primeiros de cada grupo

        # Verifica se torneio pode ser finalizado
        self.assertFalse(torneio.is_finished())  # Ainda tem playoffs pendentes

        # Finaliza torneio
        torneio.finish()
        self.assertFalse(torneio.ativo)

    def test_tournament_with_single_group(self):
        '''Testa torneio com grupo único'''
        torneio = Torneio.objects.create(
            nome='Torneio Simples',
            data=date.today(),
            quantidade_grupos=1,
            playoffs=False,
            criado_por=self.user
        )

        # Cria 3 jogadores (número ímpar para testar bye)
        jogadores = [
            Jogador.objects.create(nome=f'Jogador {i}', criado_por=self.user)
            for i in range(3)
        ]

        # Cria duplas individuais
        duplas = [
            Dupla.objects.create(jogador1=jogador, torneio=torneio, criado_por=self.user)
            for jogador in jogadores
        ]

        # Cria jogos
        jogos = torneio.create_games()

        # Com 3 duplas, deve criar 3 jogos (cada dupla joga 2 vezes)
        self.assertEqual(len(jogos), 3)

        # Testa se não há playoffs
        jogos_playoff = [j for j in jogos if not j.fase.startswith('GRUPO')]
        self.assertEqual(len(jogos_playoff), 0)

    def test_player_statistics_update(self):
        '''Testa se as estatísticas dos jogadores são atualizadas'''
        # Este é um teste conceitual - o modelo atual não atualiza
        # automaticamente as estatísticas dos jogadores
        jogador = Jogador.objects.create(nome='Teste Stats')

        # Valores iniciais
        self.assertEqual(jogador.jogos, 0)
        self.assertEqual(jogador.vitorias, 0)
        self.assertEqual(jogador.derrotas, 0)

        # TODO: Implementar lógica de atualização automática
        # quando jogos forem concluídos