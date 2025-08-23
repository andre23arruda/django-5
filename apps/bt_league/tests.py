from django.test import TestCase
from django.contrib.auth.models import User
from .models import Jogador, Torneio, Jogo

class JogadorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='12345'
        )
        self.jogador = Jogador.objects.create(
            nome='Jogador Teste',
            telefone='123456789',
            criado_por=self.user
        )

    def test_player_creation(self):
        self.assertTrue(isinstance(self.jogador, Jogador))
        self.assertEqual(self.jogador.__str__(), 'Jogador Teste')
        self.assertTrue(self.jogador.ativo)

    def test_player_points(self):
        torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data='2022-01-01',
            criado_por=self.user
        )
        jogador2 = Jogador.objects.create(
            nome='Jogador 2',
            criado_por=self.user
        )
        jogador3 = Jogador.objects.create(
            nome='Jogador 3',
            criado_por=self.user
        )
        jogador4 = Jogador.objects.create(
            nome='Jogador 4',
            criado_por=self.user
        )

        # Create a game where player wins
        jogo = Jogo.objects.create(
            torneio=torneio,
            quadra=1,
            dupla1_jogador1=self.jogador,
            dupla1_jogador2=jogador2,
            dupla2_jogador1=jogador3,
            dupla2_jogador2=jogador4,
            placar_dupla1=21,
            placar_dupla2=19,
        )
        vitorias, pontos, saldo, n_jogos = self.jogador.player_points(torneio)
        self.assertEqual(vitorias, 1)
        self.assertEqual(pontos, 21)
        self.assertEqual(saldo, 2)
        self.assertEqual(n_jogos, 1)
        self.assertEqual('C', jogo.concluido)


class TorneioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='12345'
        )
        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data='2022-01-01',
            criado_por=self.user
        )
        self.player1 = Jogador.objects.create(
            nome='Jogador 1',
            criado_por=self.user
        )
        self.player2 = Jogador.objects.create(
            nome='Jogador 2',
            criado_por=self.user
        )
        self.player3 = Jogador.objects.create(
            nome='Jogador 3',
            criado_por=self.user
        )
        self.player4 = Jogador.objects.create(
            nome='Jogador 4',
            criado_por=self.user
        )

    def test_tournament_creation(self):
        self.assertTrue(isinstance(self.torneio, Torneio))
        self.assertEqual(self.torneio.__str__(), 'Torneio Teste')
        self.assertTrue(self.torneio.ativo)

    def test_create_games(self):
        self.torneio.jogadores.add(self.player1, self.player2, self.player3, self.player4)
        self.torneio.create_games()
        self.assertEqual(Jogo.objects.filter(torneio=self.torneio).count(), 3)
        self.assertIsNone(Jogo.objects.filter(torneio=self.torneio).first().placar_dupla1)

    def test_no_game_with_insufficient_players(self):
        self.torneio.jogadores.add(self.player1, self.player2)
        self.torneio.create_games()
        self.assertEqual(Jogo.objects.filter(torneio=self.torneio).count(), 0)

    def test_game_status_concluido(self):
        self.torneio.jogadores.add(self.player1, self.player2, self.player3, self.player4)
        self.torneio.create_games()
        jogo = Jogo.objects.filter(torneio=self.torneio).first()
        jogo.placar_dupla1 = 6
        jogo.placar_dupla2 = 7
        jogo.save()
        self.assertTrue(jogo.concluido == 'C')
