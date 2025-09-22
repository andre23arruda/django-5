import json
import os
from datetime import date
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.messages import get_messages
from openpyxl import load_workbook
import io

from ..models import Jogador, Dupla, Torneio, Jogo, Ranking
from ..views import distribute_classifieds


class ViewsTestCase(TestCase):
    def setUp(self):
        '''Configuração inicial para os testes'''
        self.client = Client()

        # Usuário comum
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Superusuário
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Ranking
        self.ranking = Ranking.objects.create(
            nome='Ranking Teste',
            criado_por=self.user
        )

        # Torneio
        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date.today(),
            quantidade_grupos=2,
            criado_por=self.user,
            ranking=self.ranking
        )

        # Jogadores
        self.jogadores = []
        for i in range(4):
            jogador = Jogador.objects.create(
                nome=f'Jogador {i+1}',
                criado_por=self.user
            )
            self.jogadores.append(jogador)

        # Duplas
        self.duplas = []
        for i in range(0, 4, 2):
            dupla = Dupla.objects.create(
                jogador1=self.jogadores[i],
                jogador2=self.jogadores[i+1] if i+1 < len(self.jogadores) else None,
                torneio=self.torneio,
                criado_por=self.user
            )
            self.duplas.append(dupla)


class DistributeClassifiedsTest(TestCase):
    '''Testa a função distribute_classifieds'''

    def test_distribute_classifieds_basic(self):
        '''Testa distribuição básica de classificados'''
        classifieds = [1, 2, 3, 4, 5, 6, 7, 8]
        result = distribute_classifieds(classifieds)
        expected = [1, 8, 3, 6, 5, 4, 7, 2]
        self.assertEqual(result, expected)

    def test_distribute_classifieds_small(self):
        '''Testa com lista pequena'''
        classifieds = [1, 2, 3, 4]
        result = distribute_classifieds(classifieds)
        expected = [1, 4, 3, 2]
        self.assertEqual(result, expected)

    def test_distribute_classifieds_empty(self):
        '''Testa com lista vazia'''
        classifieds = []
        result = distribute_classifieds(classifieds)
        expected = []
        self.assertEqual(result, expected)


class CreateGamesViewTest(ViewsTestCase):
    '''Testa a view create_games'''

    def test_create_games_not_authenticated(self):
        '''Testa acesso sem autenticação'''
        url = reverse('cup:create_games', args=[self.torneio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_create_games_authenticated_success(self):
        '''Testa criação de jogos com sucesso'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('cup:create_games', args=[self.torneio.id])

        response = self.client.get(url)

        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'/admin/cup/torneio/{self.torneio.id}/change/', response.url)
        self.assertIn('#jogos-tab', response.url)

        # Verifica se jogos foram criados
        jogos = Jogo.objects.filter(torneio=self.torneio)
        self.assertGreater(jogos.count(), 0)

        # Verifica mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('sucesso' in str(m) for m in messages))

    def test_create_games_insufficient_teams(self):
        '''Testa criação de jogos com duplas insuficientes'''
        # Cria torneio com muitos grupos
        torneio_problematico = Torneio.objects.create(
            nome='Torneio Problema',
            data=date.today(),
            quantidade_grupos=8,  # Muitos grupos para poucas duplas
            criado_por=self.user
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('cup:create_games', args=[torneio_problematico.id])

        response = self.client.get(url)

        # Verifica mensagem de erro
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.level_tag == 'error' for msg in messages))

    def test_create_games_torneio_not_found(self):
        '''Testa com torneio inexistente'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('cup:create_games', args=['inexistente'])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class FinishTournamentViewTest(ViewsTestCase):
    '''Testa a view finish_tournament'''

    def test_finish_tournament_success(self):
        '''Testa finalização de torneio'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('cup:finish_tournament', args=[self.torneio.id])

        # Verifica que o torneio está ativo inicialmente
        self.assertTrue(self.torneio.ativo)

        response = self.client.get(url)

        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)

        # Verifica se o torneio foi finalizado
        self.torneio.refresh_from_db()
        self.assertFalse(self.torneio.ativo)

        # Verifica mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('finalizado' in str(m) for m in messages))


class NextStageViewTest(ViewsTestCase):
    '''Testa a view next_stage'''

    def test_next_stage_not_authenticated(self):
        '''Testa acesso sem autenticação'''
        url = reverse('cup:next_stage', args=[self.torneio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_next_stage_groups_not_finished(self):
        '''Testa com jogos de grupo não finalizados'''
        # Cria alguns jogos de grupo não finalizados
        Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.duplas[0],
            dupla2=self.duplas[1],
            fase='GRUPO 1',
            concluido='P'  # Pendente
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('cup:next_stage', args=[self.torneio.id])

        response = self.client.get(url)

        # Verifica mensagem de erro
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('não foram finalizados' in str(m) for m in messages))

    def test_next_stage_process_groups(self):
        '''Testa processamento de grupos'''
        # Cria jogos de grupo finalizados
        jogo1 = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.duplas[0],
            dupla2=self.duplas[1],
            fase='GRUPO 1',
            pontos_dupla1=15,
            pontos_dupla2=10,
            concluido='C'
        )

        jogo2 = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.duplas[0],
            dupla2=self.duplas[1],
            fase='GRUPO 2',
            pontos_dupla1=12,
            pontos_dupla2=8,
            concluido='C'
        )

        # Cria jogos de semifinal vazios
        Jogo.objects.create(
            torneio=self.torneio,
            fase='SEMIFINAIS'
        )
        Jogo.objects.create(
            torneio=self.torneio,
            fase='SEMIFINAIS'
        )
        Jogo.objects.create(
            torneio=self.torneio,
            fase='FINAL'
        )

        self.client.login(username='testuser', password='testpass123')
        url = reverse('cup:next_stage', args=[self.torneio.id])

        response = self.client.get(url)

        # Verifica se semifinais foram preenchidas
        semifinais = Jogo.objects.filter(torneio=self.torneio, fase='SEMIFINAIS')
        for semi in semifinais:
            self.assertIsNotNone(semi.dupla1)
            self.assertIsNotNone(semi.dupla2)


class SeeTournamentViewTest(ViewsTestCase):
    '''Testa a view see_tournament'''

    def test_see_tournament_success(self):
        '''Testa visualização de torneio'''
        # Cria alguns jogos
        Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.duplas[0],
            dupla2=self.duplas[1],
            fase='GRUPO 1',
            pontos_dupla1=15,
            pontos_dupla2=10,
            concluido='C'
        )

        url = reverse('cup:see_tournament', args=[self.torneio.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.torneio.nome)
        self.assertIn('torneio', response.context)
        self.assertIn('grupos', response.context)
        self.assertIn('fases_finais', response.context)

    def test_see_tournament_permissions(self):
        '''Testa permissões de edição'''
        # Testa com usuário criador
        self.client.login(username='testuser', password='testpass123')
        url = reverse('cup:see_tournament', args=[self.torneio.id])
        response = self.client.get(url)

        self.assertTrue(response.context['can_edit'])

        # Testa com superusuário
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(url)
        self.assertTrue(response.context['can_edit'])

        # Testa sem login
        self.client.logout()
        response = self.client.get(url)
        self.assertFalse(response.context['can_edit'])


class QRCodeTournamentViewTest(ViewsTestCase):
    '''Testa a view qrcode_tournament'''

    @patch.dict(os.environ, {'APP_LINK': 'http://testserver'})
    def test_qrcode_tournament_authenticated(self):
        '''Testa geração de QR Code com usuário autenticado'''
        self.client.login(username='testuser', password='testpass123')
        url = reverse('cup:qrcode_tournament', args=[self.torneio.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('img_b64', response.context)
        self.assertIn('torneio', response.context)
        self.assertEqual(response.context['torneio'], self.torneio)

    def test_qrcode_tournament_not_authenticated(self):
        '''Testa acesso sem autenticação'''
        url = reverse('cup:qrcode_tournament', args=[self.torneio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)


class GetTournamentDataViewTest(ViewsTestCase):
    '''Testa a view get_tournament_data (API JSON)'''

    def test_get_tournament_data_success(self):
        '''Testa retorno de dados JSON do torneio'''
        # Cria alguns jogos para teste
        Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.duplas[0],
            dupla2=self.duplas[1],
            fase='GRUPO 1',
            pontos_dupla1=15,
            pontos_dupla2=10,
            concluido='C'
        )

        Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.duplas[0],
            dupla2=self.duplas[1],
            fase='FINAL'
        )

        url = reverse('cup:tournament_data', args=[self.torneio.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = json.loads(response.content)

        # Verifica estrutura da resposta
        self.assertIn('torneio', data)
        self.assertIn('grupos', data)
        self.assertIn('fases_finais', data)
        self.assertIn('groups_finished', data)
        self.assertIn('can_edit', data)

        # Verifica dados do torneio
        self.assertEqual(data['torneio']['nome'], self.torneio.nome)
        self.assertEqual(data['torneio']['id'], self.torneio.id)

        # Verifica se tem dados de grupos
        self.assertIn('GRUPO 1', data['grupos'])

        # Verifica se tem dados de fases finais
        self.assertIn('FINAL', data['fases_finais'])

    def test_get_tournament_data_not_found(self):
        '''Testa com torneio inexistente'''
        url = reverse('cup:tournament_data', args=['slug-inexistente'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_get_tournament_data_permissions(self):
        '''Testa permissões no JSON'''
        # Sem login
        url = reverse('cup:tournament_data', args=[self.torneio.slug])
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertFalse(data['can_edit'])

        # Com login do criador
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertTrue(data['can_edit'])


class IntegrationViewsTest(ViewsTestCase):
    '''Testes de integração das views'''

    def test_complete_tournament_workflow(self):
        '''Testa fluxo completo de um torneio através das views'''
        self.client.login(username='testuser', password='testpass123')

        # 1. Criar jogos
        create_url = reverse('cup:create_games', args=[self.torneio.id])
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 302)

        # Verifica se jogos foram criados
        jogos = Jogo.objects.filter(torneio=self.torneio)
        self.assertGreater(jogos.count(), 0)

        # 2. Simular alguns resultados nos grupos
        jogos_grupo = jogos.filter(fase__startswith='GRUPO')
        for jogo in jogos_grupo:
            jogo.pontos_dupla1 = 15
            jogo.pontos_dupla2 = 10
            jogo.save()

        # 3. Avançar para próxima fase
        next_stage_url = reverse('cup:next_stage', args=[self.torneio.id])
        response = self.client.get(next_stage_url)
        self.assertEqual(response.status_code, 302)

        # 4. Visualizar torneio
        see_url = reverse('cup:see_tournament', args=[self.torneio.id])
        response = self.client.get(see_url)
        self.assertEqual(response.status_code, 200)

        # 5. Obter dados JSON
        api_url = reverse('cup:tournament_data', args=[self.torneio.slug])
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        # 6. Exportar para Excel
        export_url = reverse('cup:download', args=[self.torneio.id])
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 200)

        # 7. Finalizar torneio
        finish_url = reverse('cup:finish_tournament', args=[self.torneio.id])
        response = self.client.get(finish_url)
        self.assertEqual(response.status_code, 302)

        # Verifica se torneio foi finalizado
        self.torneio.refresh_from_db()
        self.assertFalse(self.torneio.ativo)

    def test_error_handling(self):
        '''Testa tratamento de erros em várias views'''
        self.client.login(username='testuser', password='testpass123')

        # Torneio inexistente
        invalid_id = 'invalid-id'

        urls_to_test = [
            ('cup:create_games', [invalid_id]),
            ('cup:finish_tournament', [invalid_id]),
            ('cup:next_stage', [invalid_id]),
            ('cup:see_tournament', [invalid_id]),
            ('cup:qrcode_tournament', [invalid_id]),
            ('cup:download', [invalid_id]),
        ]

        for url_name, args in urls_to_test:
            url = reverse(url_name, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, f'URL {url_name} should return 404')

    def test_authentication_requirements(self):
        '''Testa requisitos de autenticação'''
        # URLs que requerem autenticação
        auth_required_urls = [
            ('cup:create_games', [self.torneio.id]),
            ('cup:next_stage', [self.torneio.id]),
            ('cup:qrcode_tournament', [self.torneio.id]),
        ]

        for url_name, args in auth_required_urls:
            url = reverse(url_name, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f'URL {url_name} should require authentication')
            self.assertIn('/admin/login/', response.url)

        # URLs que NÃO requerem autenticação
        public_urls = [
            ('cup:see_tournament', [self.torneio.id]),
            ('cup:tournament_data', [self.torneio.slug]),
            ('cup:download', [self.torneio.id]),
        ]

        for url_name, args in public_urls:
            url = reverse(url_name, args=args)
            response = self.client.get(url)
            self.assertNotEqual(response.status_code, 302, f'URL {url_name} should be public')
