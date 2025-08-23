from django.test import TestCase
from django.contrib.auth.models import User
from .models import Dupla, Torneio, Jogo

class DuplaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='12345'
        )
        self.dupla = Dupla.objects.create(
            jogador1='Jogador 1',
            jogador2='Jogador 2',
            telefone='123456789',
            criado_por=self.user
        )

    def test_dupla_creation(self):
        self.assertTrue(isinstance(self.dupla, Dupla))
        self.assertEqual(
            self.dupla.__str__(),
            'Jogador 1/Jogador 2'
        )
        self.assertTrue(self.dupla.ativo)

    def test_render_method(self):
        self.assertEqual(
            self.dupla.render(),
            'Jogador 1<br/>Jogador 2'
        )


class TorneioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='12345'
        )
        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data='2022-01-01',
            criado_por=self.user,
            quantidade_grupos=2
        )
        # Create test doubles
        self.duplas = []
        for i in range(8):  # Create 8 doubles for 2 groups
            dupla = Dupla.objects.create(
                jogador1=f'Jogador {i*2+1}',
                jogador2=f'Jogador {i*2+2}',
                criado_por=self.user
            )
            self.duplas.append(dupla)
            self.torneio.duplas.add(dupla)

    def test_torneio_creation(self):
        self.assertTrue(isinstance(self.torneio, Torneio))
        self.assertEqual(self.torneio.__str__(), 'Torneio Teste')
        self.assertTrue(self.torneio.ativo)

    def test_create_games(self):
        self.torneio.create_games()
        games_count = Jogo.objects.filter(
            torneio=self.torneio,
            fase__startswith='GRUPO'
        ).count()
        expected_games = 12
        self.assertEqual(games_count, expected_games)

    def test_game_status_concluido(self):
        self.torneio.create_games()
        game = Jogo.objects.filter(
            torneio=self.torneio,
            fase__startswith='GRUPO'
        ).first()
        game.placar_dupla1 = 6
        game.placar_dupla2 = 7
        game.save()
        self.assertTrue(game.concluido == 'C')

    def test_game_winner(self):
        self.torneio.create_games()
        game = Jogo.objects.filter(
            torneio=self.torneio,
            fase__startswith='GRUPO'
        ).first()
        game.placar_dupla1 = 6
        game.placar_dupla2 = 7
        game.save()
        self.assertEqual(game.winner, game.dupla2)

    def test_get_groups_ranking(self):
        self.torneio.create_games()
        games = Jogo.objects.filter(torneio=self.torneio)
        game1 = games[0]
        game1.placar_dupla1 = 21
        game1.placar_dupla2 = 19
        game1.concluido = 'C'
        game1.save()

        game2 = games[1]
        game2.placar_dupla1 = 10
        game2.placar_dupla2 = 9
        game2.concluido = 'C'
        game2.save()

        ranking = self.torneio.get_groups_ranking()
        self.assertTrue('GRUPO 1' in ranking)
        self.assertTrue('GRUPO 2' in ranking)
        group1_ranking = ranking['GRUPO 1']
        self.assertTrue(game1.dupla1 == group1_ranking[0]['dupla'])
        self.assertTrue(game2.dupla1 == group1_ranking[1]['dupla'])
        self.assertTrue(group1_ranking[0]['pontos'] > group1_ranking[1]['pontos'])