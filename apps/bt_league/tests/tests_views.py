import json, os
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Ranking, Jogador, Torneio, Jogo
from datetime import date


class CreateGamesViewTest(TestCase):
    '''Testes para a view create_games'''
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date(2025, 10, 22),
            criado_por=self.user
        )

        # Criar 8 jogadores
        for i in range(8):
            jogador = Jogador.objects.create(nome=f'Jogador {i+1}', criado_por=self.user)
            self.torneio.jogadores.add(jogador)

    def test_create_games_requires_login(self):
        '''Testa que a view requer autenticação'''
        url = reverse('bt_league:create_games', args=[self.torneio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_create_games_success(self):
        '''Testa criação de jogos com sucesso'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('bt_league:create_games', args=[self.torneio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Jogo.objects.filter(torneio=self.torneio).exists())

    def test_create_games_invalid_player_count(self):
        '''Testa criação de jogos com número inválido de jogadores'''
        # Adicionar 1 jogador (total = 9)
        jogador = Jogador.objects.create(nome='Extra', criado_por=self.user)
        self.torneio.jogadores.add(jogador)
        self.client.login(username='testuser', password='testpass123')
        url = reverse('bt_league:create_games', args=[self.torneio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_create_games_nonexistent_tournament(self):
        '''Testa acesso a torneio inexistente'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('bt_league:create_games', args=['invalid-id'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class FinishTournamentViewTest(TestCase):
    '''Testes para a view finish_tournament'''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date(2025, 10, 22),
            criado_por=self.user,
            ativo=True
        )

    def test_finish_tournament_success(self):
        '''Testa finalização de torneio'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('bt_league:finish_tournament', args=[self.torneio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.torneio.refresh_from_db()
        self.assertFalse(self.torneio.ativo)

    def test_finish_tournament_nonexistent(self):
        '''Testa finalização de torneio inexistente'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('bt_league:finish_tournament', args=['invalid-id'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class QRCodeTournamentViewTest(TestCase):
    '''Testa a view qrcode_tournament'''
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date(2025, 10, 22),
            criado_por=self.user,
            ativo=True
        )

    @patch.dict(os.environ, {'APP_LINK': 'http://testserver'})
    def test_qrcode_tournament_authenticated(self):
        '''Testa geração de QR Code com usuário autenticado'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('bt_league:qrcode_tournament', args=[self.torneio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('img_b64', response.context)
        self.assertIn('torneio', response.context)
        self.assertEqual(response.context['torneio'], self.torneio)

    def test_qrcode_tournament_not_authenticated(self):
        '''Testa acesso sem autenticação'''
        url = reverse('bt_league:qrcode_tournament', args=[self.torneio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_qrcode_not_found(self):
        '''Testa com torneio inexistente'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('bt_league:qrcode_tournament', args=['invalid-id'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class SeeTournamentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date(2025, 10, 22),
            criado_por=self.user,
            quadras=1
        )

        # Criar jogadores
        self.jogador1 = Jogador.objects.create(nome='Jogador 1', criado_por=self.user)
        self.jogador2 = Jogador.objects.create(nome='Jogador 2', criado_por=self.user)
        self.jogador3 = Jogador.objects.create(nome='Jogador 3', criado_por=self.user)
        self.jogador4 = Jogador.objects.create(nome='Jogador 4', criado_por=self.user)

        self.torneio.jogadores.add(
            self.jogador1, self.jogador2, self.jogador3, self.jogador4
        )
        self.torneio.create_games()
        self.jogo1 = self.torneio.jogo_set.first()
        self.jogo1.placar_dupla1 = 10
        self.jogo1.placar_dupla2 = 8
        self.jogo1.save()
        self.jogo2 = self.torneio.jogo_set.last()
        self.jogo2.placar_dupla1 = 12
        self.jogo2.placar_dupla2 = 10
        self.jogo2.save()

        self.url = reverse('bt_league:see_tournament', args=[self.torneio.id])

    def test_see_tournament_success(self):
        '''Testa visualização do torneio'''
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bt_league/see_league.html')

    def test_see_tournament_context(self):
        '''Testa contexto da view'''
        response = self.client.get(self.url)
        self.assertIn('torneio', response.context)
        self.assertIn('jogos', response.context)
        self.assertIn('ranking', response.context)
        self.assertIn('n_jogos', response.context)
        self.assertIn('jogos_restantes', response.context)
        self.assertIn('can_edit', response.context)
        self.assertEqual(response.context['torneio'], self.torneio)
        self.assertEqual(response.context['n_jogos'], 3) # 3 jogos criados, pois são 4 jogadores
        self.assertEqual(response.context['jogos_restantes'], 1) # 1, pois dois jogos estão com placares definidos


class GetTournamentDataViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date(2025, 10, 22),
            criado_por=self.user,
            quadras=1
        )

        # Criar jogadores
        self.jogador1 = Jogador.objects.create(nome='Jogador 1', criado_por=self.user)
        self.jogador2 = Jogador.objects.create(nome='Jogador 2', criado_por=self.user)
        self.jogador3 = Jogador.objects.create(nome='Jogador 3', criado_por=self.user)
        self.jogador4 = Jogador.objects.create(nome='Jogador 4', criado_por=self.user)

        self.torneio.jogadores.add(
            self.jogador1, self.jogador2, self.jogador3, self.jogador4
        )
        self.torneio.create_games()
        self.jogo1 = self.torneio.jogo_set.first()
        self.jogo1.placar_dupla1 = 10
        self.jogo1.placar_dupla2 = 8
        self.jogo1.save()
        self.jogo2 = self.torneio.jogo_set.last()
        self.jogo2.placar_dupla1 = 12
        self.jogo2.placar_dupla2 = 10
        self.jogo2.save()

        self.url = reverse('bt_league:tournament_data', args=[self.torneio.slug])

    def test_get_tournament_data_success(self):
        '''Testa obtenção de dados do torneio'''
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_get_tournament_data_structure(self):
        '''Testa estrutura do JSON retornado'''
        response = self.client.get(self.url)
        data = json.loads(response.content)
        self.assertIn('torneio', data)
        self.assertIn('jogos', data)
        self.assertIn('estatisticas', data)
        self.assertIn('ranking', data)
        self.assertIn('can_edit', data)

    def test_get_tournament_data_torneio_fields(self):
        '''Testa campos do torneio no JSON'''
        response = self.client.get(self.url)
        data = json.loads(response.content)
        torneio_data = data['torneio']
        self.assertEqual(torneio_data['id'], self.torneio.id)
        self.assertEqual(torneio_data['nome'], 'Torneio Teste')
        self.assertEqual(torneio_data['ativo'], True)
        self.assertIn('data', torneio_data)

    def test_get_tournament_data_jogos_structure(self):
        '''Testa estrutura dos jogos no JSON'''
        response = self.client.get(self.url)
        data = json.loads(response.content)
        jogos = data['jogos']
        self.assertEqual(len(jogos), 3) # 3 jogos criados, pois são 4 jogadores

        jogo = jogos[0]
        self.assertIn('id', jogo)
        self.assertIn('dupla1', jogo)
        self.assertIn('dupla2', jogo)
        self.assertIn('placar_dupla1', jogo)
        self.assertIn('placar_dupla2', jogo)
        self.assertIn('concluido', jogo)
        self.assertIn('quadra', jogo)

    def test_get_tournament_data_estatisticas(self):
        '''Testa estatísticas no JSON'''
        response = self.client.get(self.url)
        data = json.loads(response.content)
        estatisticas = data['estatisticas']
        self.assertEqual(estatisticas['total_jogos'], 3)
        self.assertEqual(estatisticas['jogos_restantes'], 1) # 1 pois, dois jogos está com placares definidos

    def test_get_tournament_data_ranking_structure(self):
        '''Testa estrutura do ranking no JSON'''
        response = self.client.get(self.url)
        data = json.loads(response.content)

        ranking = data['ranking']
        self.assertTrue(len(ranking) > 0)

        jogador_rank = ranking[0]
        self.assertIn('jogador', jogador_rank)
        self.assertIn('pontos', jogador_rank)
        self.assertIn('saldo', jogador_rank)
        self.assertIn('vitorias', jogador_rank)
        self.assertIn('jogos', jogador_rank)
        self.assertIn('posicao', jogador_rank)

    def test_get_tournament_data_can_edit_anonymous(self):
        '''Testa can_edit para usuário anônimo'''
        response = self.client.get(self.url)
        data = json.loads(response.content)
        self.assertFalse(data['can_edit'])

    def test_get_tournament_data_can_edit_owner(self):
        '''Testa can_edit para o dono do torneio'''
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        data = json.loads(response.content)
        self.assertTrue(data['can_edit'])

    def test_get_tournament_data_can_edit_superuser(self):
        '''Testa can_edit para superuser'''
        self.client.login(username='admin', password='admin123')
        response = self.client.get(self.url)
        data = json.loads(response.content)
        self.assertTrue(data['can_edit'])

    def test_get_tournament_data_not_found(self):
        '''Testa com torneio inexistente'''
        url = reverse('bt_league:tournament_data', args=['invalid-slug'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Torneio não encontrado')

    def test_get_tournament_data_ranking_order(self):
        '''Testa ordenação do ranking no JSON'''
        response = self.client.get(self.url)
        data = json.loads(response.content)
        ranking = data['ranking']

        # Verificar ordenação
        for i in range(len(ranking) - 1):
            atual = ranking[i]
            proximo = ranking[i + 1]

            if atual['vitorias'] == proximo['vitorias']:
                if atual['saldo'] == proximo['saldo']:
                    self.assertGreaterEqual(atual['pontos'], proximo['pontos'])
                else:
                    self.assertGreaterEqual(atual['saldo'], proximo['saldo'])
            else:
                self.assertGreaterEqual(atual['vitorias'], proximo['vitorias'])


class ViewsIntegrationTest(TestCase):
    '''Testes de integração entre as views'''

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.torneio = Torneio.objects.create(
            nome='Torneio Integração',
            data=date(2025, 10, 22),
            criado_por=self.user,
            quadras=1
        )

        # Criar 4 jogadores
        for i in range(4):
            jogador = Jogador.objects.create(
                nome=f'Jogador {i+1}',
                criado_por=self.user
            )
            self.torneio.jogadores.add(jogador)

    def test_complete_tournament_workflow(self):
        '''Testa fluxo completo: criar jogos -> ver torneio -> finalizar'''
        self.client.login(username='testuser', password='testpass123')

        # 1. Criar jogos
        create_url = reverse('bt_league:create_games', args=[self.torneio.id])
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 302)

        # 2. Ver torneio
        see_url = reverse('bt_league:see_tournament', args=[self.torneio.id])
        response = self.client.get(see_url)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.context['n_jogos'], 0)

        # 3. Obter dados JSON
        data_url = reverse('bt_league:tournament_data', args=[self.torneio.slug])
        response = self.client.get(data_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreater(len(data['jogos']), 0)

        # 4. Finalizar torneio
        finish_url = reverse('bt_league:finish_tournament', args=[self.torneio.id])
        response = self.client.get(finish_url)
        self.assertEqual(response.status_code, 302)

        self.torneio.refresh_from_db()
        self.assertFalse(self.torneio.ativo)

    def test_error_handling(self):
        '''Testa tratamento de erros em várias views'''
        self.client.login(username='testuser', password='testpass123')

        # Torneio inexistente
        invalid_id = 'invalid-id'

        urls_to_test = [
            ('bt_league:create_games', [invalid_id]),
            ('bt_league:finish_tournament', [invalid_id]),
            ('bt_league:see_tournament', [invalid_id]),
            ('bt_league:qrcode_tournament', [invalid_id]),
            ('bt_league:download', [invalid_id]),
        ]

        for url_name, args in urls_to_test:
            url = reverse(url_name, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, f'URL {url_name} should return 404')

    def test_authentication_requirements(self):
        '''Testa requisitos de autenticação'''
        # URLs que requerem autenticação
        auth_required_urls = [
            ('bt_league:create_games', [self.torneio.id]),
            ('bt_league:qrcode_tournament', [self.torneio.id]),
        ]

        for url_name, args in auth_required_urls:
            url = reverse(url_name, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f'URL {url_name} should require authentication')
            self.assertIn('/admin/login/', response.url)

        # URLs que NÃO requerem autenticação
        public_urls = [
            ('bt_league:see_tournament', [self.torneio.id]),
            ('bt_league:tournament_data', [self.torneio.slug]),
            ('bt_league:download', [self.torneio.id]),
        ]

        for url_name, args in public_urls:
            url = reverse(url_name, args=args)
            response = self.client.get(url)
            self.assertNotEqual(response.status_code, 302, f'URL {url_name} should be public')
