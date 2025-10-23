from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Ranking, Jogador, Torneio, Jogo


class RankingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.group = Group.objects.create(name='Test Group')
        self.ranking = Ranking.objects.create(
            nome='Ranking Teste',
            criado_por=self.user,
            grupo_criador=self.group
        )

    def test_create_ranking(self):
        '''Testa a criação de um ranking'''
        ranking = Ranking.objects.create(
            nome='Novo Ranking',
            criado_por=self.user
        )
        self.assertIsNotNone(ranking.id)
        self.assertEqual(ranking.nome, 'Novo Ranking')
        self.assertTrue(ranking.ativo)
        self.assertIsNotNone(ranking.criado_em)
        self.assertIsNotNone(ranking.slug)

    def test_ranking_str_representation(self):
        '''Testa a representação string do ranking'''
        self.assertEqual(str(self.ranking), 'Ranking Teste')

    def test_ranking_slug_generation(self):
        '''Testa a geração automática do slug'''
        ranking = Ranking.objects.create(
            nome='Ranking com Espaços',
            criado_por=self.user
        )
        self.assertIn('ranking-com-espacos', ranking.slug)
        self.assertIn(ranking.id, ranking.slug)

    def test_ranking_slug_uniqueness(self):
        '''Testa unicidade do slug'''
        ranking1 = Ranking.objects.create(nome='Mesmo Nome', criado_por=self.user)
        ranking2 = Ranking.objects.create(nome='Mesmo Nome', criado_por=self.user)
        self.assertNotEqual(ranking1.slug, ranking2.slug)

    def test_ranking_default_ativo(self):
        '''Testa que ativo é True por padrão'''
        ranking = Ranking.objects.create(nome='Ranking Ativo', criado_por=self.user)
        self.assertTrue(ranking.ativo)

    def test_ranking_ordering(self):
        '''Testa a ordenação por nome'''
        Ranking.objects.create(nome='Zebra', criado_por=self.user)
        Ranking.objects.create(nome='Abelha', criado_por=self.user)
        rankings = Ranking.objects.all()
        self.assertEqual(rankings[0].nome, 'Abelha')

    def test_ranking_with_null_user(self):
        '''Testa ranking com usuário nulo (SET_NULL)'''
        ranking = Ranking.objects.create(nome='Ranking Órfão', criado_por=self.user)
        ranking.criado_por.delete()
        ranking.refresh_from_db()
        self.assertIsNone(ranking.criado_por)


class JogadorModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.jogador = Jogador.objects.create(
            nome='João Silva',
            email='joao@example.com',
            telefone='11999999999',
            criado_por=self.user
        )

    def test_create_jogador(self):
        '''Testa a criação de um jogador'''
        jogador = Jogador.objects.create(
            nome='Maria Santos',
            email='maria@example.com',
            criado_por=self.user
        )
        self.assertIsNotNone(jogador.id)
        self.assertEqual(jogador.nome, 'Maria Santos')
        self.assertTrue(jogador.ativo)
        self.assertIsNotNone(jogador.criado_em)

    def test_jogador_str_representation(self):
        '''Testa a representação string do jogador'''
        self.assertEqual(str(self.jogador), 'João Silva')

    def test_jogador_short_name_with_surname(self):
        '''Testa short_name com nome e sobrenome'''
        result = self.jogador.short_name()
        self.assertEqual(result, 'J. Silva')

    def test_jogador_short_name_single_name(self):
        '''Testa short_name com nome único'''
        jogador = Jogador.objects.create(nome='Pedro', criado_por=self.user)
        result = jogador.short_name()
        self.assertEqual(result, 'Pedro')

    def test_jogador_short_name_multiple_names(self):
        '''Testa short_name com múltiplos nomes'''
        jogador = Jogador.objects.create(
            nome='João Pedro da Silva Santos',
            criado_por=self.user
        )
        result = jogador.short_name()
        self.assertEqual(result, 'J. Pedro')

    def test_jogador_default_ativo(self):
        '''Testa que ativo é True por padrão'''
        jogador = Jogador.objects.create(nome='Carlos', criado_por=self.user)
        self.assertTrue(jogador.ativo)

    def test_jogador_optional_fields(self):
        '''Testa campos opcionais'''
        jogador = Jogador.objects.create(nome='Ana', criado_por=self.user)
        self.assertIsNone(jogador.email)
        self.assertIsNone(jogador.telefone)
        self.assertIsNone(jogador.grupo_criador)

    def test_jogador_ordering(self):
        '''Testa ordenação por nome'''
        Jogador.objects.create(nome='Zebra', criado_por=self.user)
        Jogador.objects.create(nome='Abelha', criado_por=self.user)
        jogadores = Jogador.objects.all()
        self.assertEqual(jogadores[0].nome, 'Abelha')


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
        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date(2025, 10, 22),
            criado_por=self.user,
            quadras=2,
            ranking=self.ranking
        )

        # Criar jogadores para testes
        self.jogadores = []
        for i in range(8):
            jogador = Jogador.objects.create(
                nome=f'Jogador {i+1}',
                criado_por=self.user
            )
            self.jogadores.append(jogador)
            self.torneio.jogadores.add(jogador)

    def test_create_torneio(self):
        '''Testa a criação de um torneio'''
        torneio = Torneio.objects.create(
            nome='Novo Torneio',
            data=date(2025, 11, 15),
            criado_por=self.user
        )
        self.assertIsNotNone(torneio.id)
        self.assertEqual(torneio.nome, 'Novo Torneio')
        self.assertTrue(torneio.ativo)
        self.assertEqual(torneio.quadras, 1)
        self.assertIsNotNone(torneio.slug)

    def test_torneio_str_representation(self):
        '''Testa a representação string do torneio'''
        self.assertEqual(str(self.torneio), 'Torneio Teste')

    def test_torneio_slug_generation(self):
        '''Testa a geração automática do slug'''
        torneio = Torneio.objects.create(
            nome='Torneio com Espaços',
            data=date(2025, 12, 1),
            criado_por=self.user
        )
        self.assertIn('torneio-com-espacos', torneio.slug)
        self.assertIn(torneio.id, torneio.slug)

    def test_torneio_ordering(self):
        '''Testa ordenação por data decrescente'''
        Torneio.objects.create(nome='Antigo', data=date(2024, 1, 1), criado_por=self.user)
        Torneio.objects.create(nome='Recente', data=date(2025, 12, 31), criado_por=self.user)
        torneios = Torneio.objects.all()
        self.assertEqual(torneios[0].nome, 'Recente')

    def test_shuffle_players(self):
        '''Testa embaralhamento de jogadores com seed fixo'''
        jogadores1 = self.torneio.shuffle_players()
        jogadores2 = self.torneio.shuffle_players()

        # Com seed fixo, o resultado deve ser o mesmo
        self.assertEqual(jogadores1, jogadores2)
        self.assertEqual(len(jogadores1), 8)

    def test_has_games_false(self):
        '''Testa has_games quando não há jogos'''
        self.assertFalse(self.torneio.has_games())

    def test_has_games_true(self):
        '''Testa has_games quando há jogos'''
        self.torneio.create_games()
        self.assertTrue(self.torneio.has_games())

    def test_create_games_success(self):
        '''Testa criação de jogos com número válido de jogadores'''
        jogos = self.torneio.create_games()
        self.assertIsInstance(jogos, list)
        self.assertTrue(len(jogos) > 0)
        self.assertEqual(Jogo.objects.filter(torneio=self.torneio).count(), len(jogos))

    def test_create_games_invalid_player_count(self):
        '''Testa criação de jogos com número inválido de jogadores'''
        # Adicionar mais um jogador (total = 9, não múltiplo de 4)
        jogador = Jogador.objects.create(nome='Jogador Extra', criado_por=self.user)
        self.torneio.jogadores.add(jogador)
        result = self.torneio.create_games()
        self.assertIsInstance(result, Exception)

    def test_create_games_deletes_existing(self):
        '''Testa que criar jogos deleta os jogos existentes'''
        self.torneio.create_games()
        count_initial = Jogo.objects.filter(torneio=self.torneio).count()
        id_jogo_1 = Jogo.objects.filter(torneio=self.torneio).first().id

        self.torneio.create_games()
        count_after = Jogo.objects.filter(torneio=self.torneio).count()
        id_jogo_2 = Jogo.objects.filter(torneio=self.torneio).first().id

        self.assertEqual(count_initial, count_after)
        self.assertNotEqual(id_jogo_1, id_jogo_2)

    def test_is_finished_false(self):
        '''Testa is_finished quando há jogos pendentes'''
        self.torneio.create_games()
        self.assertFalse(self.torneio.is_finished())

    def test_is_finished_true(self):
        '''Testa is_finished quando todos os jogos estão concluídos'''
        self.torneio.create_games()
        Jogo.objects.filter(torneio=self.torneio).update(
            placar_dupla1=10,
            placar_dupla2=8,
            concluido='C'
        )
        self.assertTrue(self.torneio.is_finished())

    def test_finish_torneio(self):
        '''Testa finalização do torneio'''
        self.torneio.finish()
        self.torneio.refresh_from_db()
        self.assertFalse(self.torneio.ativo)


class JogoModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date(2025, 10, 22),
            criado_por=self.user
        )

        self.jogador1 = Jogador.objects.create(nome='João Silva', criado_por=self.user)
        self.jogador2 = Jogador.objects.create(nome='Maria Santos', criado_por=self.user)
        self.jogador3 = Jogador.objects.create(nome='Pedro Oliveira', criado_por=self.user)
        self.jogador4 = Jogador.objects.create(nome='Ana Costa', criado_por=self.user)

        self.jogo = Jogo.objects.create(
            torneio=self.torneio,
            quadra=1,
            dupla1_jogador1=self.jogador1,
            dupla1_jogador2=self.jogador2,
            dupla2_jogador1=self.jogador3,
            dupla2_jogador2=self.jogador4
        )

    def test_create_jogo(self):
        '''Testa a criação de um jogo'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            quadra=2,
            dupla1_jogador1=self.jogador1,
            dupla1_jogador2=self.jogador2,
            dupla2_jogador1=self.jogador3,
            dupla2_jogador2=self.jogador4
        )

        self.assertIsNotNone(jogo.id)
        self.assertEqual(jogo.concluido, 'P')
        self.assertEqual(jogo.quadra, 2)
        self.assertIsNone(jogo.placar_dupla1)
        self.assertIsNone(jogo.placar_dupla2)

    def test_jogo_str_representation(self):
        '''Testa a representação string do jogo'''
        result = str(self.jogo)
        self.assertIn('J. Silva', result)
        self.assertIn('M. Santos', result)
        self.assertIn('P. Oliveira', result)
        self.assertIn('A. Costa', result)

    def test_jogo_default_status(self):
        '''Testa status padrão do jogo'''
        self.assertEqual(self.jogo.concluido, 'P')

    def test_jogo_auto_complete_on_score(self):
        '''Testa que jogo é marcado como concluído ao adicionar placar'''
        self.jogo.placar_dupla1 = 10
        self.jogo.placar_dupla2 = 8
        self.jogo.save()

        self.assertEqual(self.jogo.concluido, 'C')

    def test_jogo_status_andamento(self):
        '''Testa que status 'A' (andamento) é mantido'''
        self.jogo.concluido = 'A'
        self.jogo.save()

        self.assertEqual(self.jogo.concluido, 'A')

    def test_jogo_partial_score_not_complete(self):
        '''Testa que jogo com placar parcial não é concluído'''
        self.jogo.placar_dupla1 = 10
        self.jogo.save()

        self.assertNotEqual(self.jogo.concluido, 'C')

    def test_render_dupla_1(self):
        '''Testa renderização da dupla 1'''
        result = self.jogo.render_dupla_1()
        self.assertIn('João Silva', result)
        self.assertIn('Maria Santos', result)
        self.assertIn('\n', result)

    def test_render_dupla_2(self):
        '''Testa renderização da dupla 2'''
        result = self.jogo.render_dupla_2()
        self.assertIn('Pedro Oliveira', result)
        self.assertIn('Ana Costa', result)
        self.assertIn('\n', result)


class JogadorPointsTest(TestCase):
    '''Testes específicos para cálculo de pontos dos jogadores'''

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

        self.torneio = Torneio.objects.create(
            nome='Torneio Pontos',
            data=date(2025, 10, 22),
            criado_por=self.user
        )

        self.jogador1 = Jogador.objects.create(nome='Jogador 1', criado_por=self.user)
        self.jogador2 = Jogador.objects.create(nome='Jogador 2', criado_por=self.user)
        self.jogador3 = Jogador.objects.create(nome='Jogador 3', criado_por=self.user)
        self.jogador4 = Jogador.objects.create(nome='Jogador 4', criado_por=self.user)

    def test_player_points_no_games(self):
        '''Testa pontos de jogador sem jogos'''
        vitorias, pontos, saldo, n_jogos = self.jogador1.player_points(self.torneio)

        self.assertEqual(vitorias, 0)
        self.assertEqual(pontos, 0)
        self.assertEqual(saldo, 0)
        self.assertEqual(n_jogos, 0)

    def test_player_points_with_victory(self):
        '''Testa pontos de jogador com vitória'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1_jogador1=self.jogador1,
            dupla1_jogador2=self.jogador2,
            dupla2_jogador1=self.jogador3,
            dupla2_jogador2=self.jogador4,
            placar_dupla1=10,
            placar_dupla2=6
        )

        vitorias, pontos, saldo, n_jogos = self.jogador1.player_points(self.torneio)

        self.assertEqual(vitorias, 1)
        self.assertEqual(pontos, 10)
        self.assertEqual(saldo, 4)
        self.assertEqual(n_jogos, 1)

    def test_player_points_with_loss(self):
        '''Testa pontos de jogador com derrota'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1_jogador1=self.jogador1,
            dupla1_jogador2=self.jogador2,
            dupla2_jogador1=self.jogador3,
            dupla2_jogador2=self.jogador4,
            placar_dupla1=6,
            placar_dupla2=10
        )

        vitorias, pontos, saldo, n_jogos = self.jogador1.player_points(self.torneio)

        self.assertEqual(vitorias, 0)
        self.assertEqual(pontos, 6)
        self.assertEqual(saldo, -4)
        self.assertEqual(n_jogos, 1)

    def test_player_ranking(self):
        '''Testa cálculo de ranking do jogador'''
        self.torneio.jogadores.add(self.jogador1, self.jogador2, self.jogador3, self.jogador4)

        # Criar jogos com resultados
        Jogo.objects.create(
            torneio=self.torneio,
            dupla1_jogador1=self.jogador1,
            dupla1_jogador2=self.jogador2,
            dupla2_jogador1=self.jogador3,
            dupla2_jogador2=self.jogador4,
            placar_dupla1=10,
            placar_dupla2=6
        )

        ranking = self.jogador1.ranking(self.torneio)
        self.assertIsNotNone(ranking)
        self.assertGreaterEqual(ranking, 1)
        self.assertLessEqual(ranking, 4)

    def test_admin_ranking(self):
        '''Testa função de ordenação para admin'''
        result = self.jogador1.admin_ranking(self.torneio)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[3], 'Jogador 1')