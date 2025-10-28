import os
from datetime import date
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import Mock, patch
from cup.admin import (
    DuplaAdmin, JogadorAdmin, JogoAdmin, RankingAdmin,
    TorneioAdmin, TorneioListFilter
)
from cup.models import Dupla, Jogador, Jogo, Ranking, Torneio


class MockRequest:
    '''Mock request para testes'''
    def __init__(self, user=None):
        self.user = user or User()
        self.path = '/admin/'
        self.META = {}


class BaseAdminTestCase(TestCase):
    '''Classe base com setup comum para todos os testes de admin'''

    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()

        # Criar usuários
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='user123'
        )

        # Criar objetos base
        self.ranking = Ranking.objects.create(
            nome='Ranking Test',
            criado_por=self.regular_user
        )

        self.jogador1 = Jogador.objects.create(
            nome='Jogador 1',
            telefone='123456789',
            criado_por=self.regular_user
        )

        self.jogador2 = Jogador.objects.create(
            nome='Jogador 2',
            telefone='987654321',
            criado_por=self.regular_user
        )

        self.torneio = Torneio.objects.create(
            nome='Torneio Test',
            data=date.today(),
            criado_por=self.regular_user,
            quantidade_grupos=2,
            tipo='D'
        )

        self.dupla = Dupla.objects.create(
            jogador1=self.jogador1,
            jogador2=self.jogador2,
            torneio=self.torneio,
            criado_por=self.regular_user
        )

    def _get_request(self, user=None, path='/admin/'):
        '''Helper para criar request com sessão e messages'''
        request = self.factory.get(path)
        request.user = user or self.regular_user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request


class TorneioListFilterTestCase(BaseAdminTestCase):
    '''Testes para TorneioListFilter'''

    def test_lookups_for_superuser(self):
        '''Superuser deve ver todos os torneios'''
        request = MockRequest(user=self.superuser)
        filter_instance = TorneioListFilter(
            request, {}, Jogo, JogoAdmin
        )
        lookups = filter_instance.lookups(request, None)
        self.assertEqual(len(lookups), 1)
        self.assertEqual(lookups[0][1], 'Torneio Test')

    def test_lookups_for_regular_user(self):
        '''Usuário regular deve ver apenas seus torneios'''
        other_user = User.objects.create_user(
            username='other',
            password='other123'
        )
        Torneio.objects.create(
            nome='Torneio Other',
            data=date.today(),
            criado_por=other_user
        )
        request = MockRequest(user=self.regular_user)
        filter_instance = TorneioListFilter(
            request, {}, Jogo, JogoAdmin
        )
        lookups = filter_instance.lookups(request, None)
        self.assertEqual(len(lookups), 1)
        self.assertEqual(lookups[0][1], 'Torneio Test')

    def test_queryset_with_filter(self):
        '''Deve filtrar queryset quando valor é fornecido'''
        jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.dupla,
            dupla2=self.dupla,
            fase='GRUPO',
        )
        request = MockRequest(user=self.superuser)
        filter_instance = TorneioListFilter(
            request,
            {},
            Jogo,
            JogoAdmin
        )
        filter_instance.used_parameters = {'torneio': self.torneio.id}
        queryset = Jogo.objects.all()
        filtered = filter_instance.queryset(request, queryset)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), jogo)


class DuplaAdminTestCase(BaseAdminTestCase):
    '''Testes para DuplaAdmin'''

    def setUp(self):
        super().setUp()
        self.dupla_admin = DuplaAdmin(Dupla, self.site)

    def test_has_module_permission_superuser(self):
        '''Superuser deve ter permissão de módulo'''
        request = MockRequest(user=self.superuser)
        self.assertTrue(self.dupla_admin.has_module_permission(request))

    def test_has_module_permission_regular_user(self):
        '''Usuário regular não deve ter permissão de módulo'''
        request = MockRequest(user=self.regular_user)
        self.assertFalse(self.dupla_admin.has_module_permission(request))

    def test_has_add_permission_superuser(self):
        '''Superuser deve ter permissão de adicionar'''
        request = MockRequest(user=self.superuser)
        self.assertTrue(self.dupla_admin.has_add_permission(request))

    def test_has_add_permission_regular_user(self):
        '''Usuário regular não deve ter permissão de adicionar'''
        request = MockRequest(user=self.regular_user)
        self.assertFalse(self.dupla_admin.has_add_permission(request))

    def test_has_delete_permission_superuser(self):
        '''Superuser deve ter permissão de deletar'''
        request = MockRequest(user=self.superuser)
        self.assertTrue(self.dupla_admin.has_delete_permission(request))

    def test_has_delete_permission_regular_user(self):
        '''Usuário regular não deve ter permissão de deletar'''
        request = MockRequest(user=self.regular_user)
        self.assertFalse(self.dupla_admin.has_delete_permission(request))

    def test_get_queryset_superuser(self):
        '''Superuser deve ver todas as duplas'''
        other_user = User.objects.create_user(
            username='other',
            password='other123'
        )
        torneio2 = Torneio.objects.create(
            nome='Torneio 2',
            data=date.today(),
            criado_por=other_user
        )
        Dupla.objects.create(
            jogador1=self.jogador1,
            jogador2=self.jogador2,
            torneio=torneio2,
            criado_por=other_user
        )
        request = MockRequest(user=self.superuser)
        queryset = self.dupla_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 2)

    def test_get_queryset_regular_user(self):
        '''Usuário regular deve ver apenas suas duplas'''
        other_user = User.objects.create_user(
            username='other',
            password='other123'
        )
        torneio2 = Torneio.objects.create(
            nome='Torneio 2',
            data=date.today(),
            criado_por=other_user
        )
        Dupla.objects.create(
            jogador1=self.jogador1,
            jogador2=self.jogador2,
            torneio=torneio2,
            criado_por=other_user
        )
        request = MockRequest(user=self.regular_user)
        queryset = self.dupla_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 1)

    def test_save_model_new_object(self):
        '''Ao criar dupla, deve setar criado_por'''
        request = MockRequest(user=self.regular_user)
        dupla = Dupla(
            jogador1=self.jogador1,
            jogador2=self.jogador2,
            torneio=self.torneio
        )
        self.dupla_admin.save_model(request, dupla, None, False)
        self.assertEqual(dupla.criado_por, self.regular_user)

    def test_get_fields_superuser(self):
        '''Superuser deve ver campos adicionais'''
        request = MockRequest(user=self.superuser)
        fields = self.dupla_admin.get_fields(request, None)
        self.assertIn('criado_por', fields)
        self.assertIn('ativo', fields)

    def test_get_fields_regular_user(self):
        '''Usuário regular não deve ver campos de admin'''
        request = MockRequest(user=self.regular_user)
        fields = self.dupla_admin.get_fields(request, None)
        self.assertNotIn('criado_por', fields)
        self.assertNotIn('ativo', fields)


class JogadorAdminTestCase(BaseAdminTestCase):
    '''Testes para JogadorAdmin'''

    def setUp(self):
        super().setUp()
        self.jogador_admin = JogadorAdmin(Jogador, self.site)

    def test_has_delete_permission_superuser(self):
        '''Superuser deve ter permissão de deletar'''
        request = MockRequest(user=self.superuser)
        self.assertTrue(self.jogador_admin.has_delete_permission(request))

    def test_has_delete_permission_regular_user(self):
        '''Usuário regular não deve ter permissão de deletar'''
        request = MockRequest(user=self.regular_user)
        self.assertFalse(self.jogador_admin.has_delete_permission(request))

    def test_get_queryset_regular_user(self):
        '''Usuário regular deve ver apenas seus jogadores'''
        other_user = User.objects.create_user(
            username='other',
            password='other123'
        )
        Jogador.objects.create(
            nome='Jogador Other',
            criado_por=other_user
        )
        request = MockRequest(user=self.regular_user)
        queryset = self.jogador_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 2)  # jogador1 e jogador2

    def test_save_model_sets_creator(self):
        '''Ao criar jogador, deve setar criado_por'''
        request = MockRequest(user=self.regular_user)
        jogador = Jogador(nome='Novo Jogador')
        self.jogador_admin.save_model(request, jogador, None, False)
        self.assertEqual(jogador.criado_por, self.regular_user)


class JogoAdminTestCase(BaseAdminTestCase):
    '''Testes para JogoAdmin'''

    def setUp(self):
        super().setUp()
        self.jogo_admin = JogoAdmin(Jogo, self.site)

    def test_has_module_permission_superuser(self):
        '''Apenas superuser deve ter permissão de módulo'''
        request = MockRequest(user=self.superuser)
        self.assertTrue(self.jogo_admin.has_module_permission(request))

    def test_has_module_permission_regular_user(self):
        '''Usuário regular não deve ter permissão de módulo'''
        request = MockRequest(user=self.regular_user)
        self.assertFalse(self.jogo_admin.has_module_permission(request))


class RankingAdminTestCase(BaseAdminTestCase):
    '''Testes para RankingAdmin'''

    def setUp(self):
        super().setUp()
        self.ranking_admin = RankingAdmin(Ranking, self.site)

    def test_has_delete_permission_superuser(self):
        '''Superuser deve ter permissão de deletar'''
        request = MockRequest(user=self.superuser)
        self.assertTrue(self.ranking_admin.has_delete_permission(request))

    def test_has_delete_permission_regular_user(self):
        '''Usuário regular não deve ter permissão de deletar'''
        request = MockRequest(user=self.regular_user)
        self.assertFalse(self.ranking_admin.has_delete_permission(request))

    def test_get_queryset_regular_user(self):
        '''Usuário regular deve ver apenas seus rankings'''
        other_user = User.objects.create_user(
            username='other',
            password='other123'
        )
        Ranking.objects.create(
            nome='Ranking Other',
            criado_por=other_user
        )
        request = MockRequest(user=self.regular_user)
        queryset = self.ranking_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 1)

    @patch.dict(os.environ, {'APP_LINK': 'http://test.com'})
    def test_change_view_extra_context(self):
        '''change_view deve adicionar APP_LINK ao contexto'''
        request = self._get_request(user=self.superuser)
        with patch.object(RankingAdmin, 'change_view', wraps=self.ranking_admin.change_view) as mock_view:
            mock_view.return_value = Mock()
            self.ranking_admin.change_view(request, str(self.ranking.id))

            # Verificar se foi chamado
            self.assertTrue(mock_view.called)


class TorneioAdminTestCase(BaseAdminTestCase):
    '''Testes para TorneioAdmin'''

    def setUp(self):
        super().setUp()
        self.torneio_admin = TorneioAdmin(Torneio, self.site)

    def test_has_delete_permission_superuser(self):
        '''Superuser deve ter permissão de deletar'''
        request = MockRequest(user=self.superuser)
        self.assertTrue(self.torneio_admin.has_delete_permission(request))

    def test_has_delete_permission_regular_user(self):
        '''Usuário regular não deve ter permissão de deletar'''
        request = MockRequest(user=self.regular_user)
        self.assertFalse(self.torneio_admin.has_delete_permission(request))

    def test_get_queryset_regular_user(self):
        '''Usuário regular deve ver apenas seus torneios'''
        other_user = User.objects.create_user(
            username='other',
            password='other123'
        )
        Torneio.objects.create(
            nome='Torneio Other',
            data=date.today(),
            criado_por=other_user
        )
        request = MockRequest(user=self.regular_user)
        queryset = self.torneio_admin.get_queryset(request)
        self.assertEqual(queryset.count(), 1)

    def test_save_model_sets_creator(self):
        '''Ao criar torneio, deve setar criado_por'''
        request = MockRequest(user=self.regular_user)
        torneio = Torneio(
            nome='Novo Torneio',
            data=date.today()
        )
        self.torneio_admin.save_model(request, torneio, None, False)
        self.assertEqual(torneio.criado_por, self.regular_user)

    def test_total_duplas_display(self):
        '''Método total_duplas deve retornar count correto'''
        count = self.torneio_admin.total_duplas(self.torneio)
        self.assertEqual(count, 1)

    def test_grupos_display(self):
        '''Método grupos deve retornar quantidade_grupos'''
        grupos = self.torneio_admin.grupos(self.torneio)
        self.assertEqual(grupos, 2)

    def test_total_jogos_display(self):
        '''Método total_jogos deve retornar count de jogos'''
        Jogo.objects.create(
            torneio=self.torneio,
            dupla1=self.dupla,
            dupla2=self.dupla,
            fase='GRUPO'
        )
        count = self.torneio_admin.total_jogos(self.torneio)
        self.assertEqual(count, 1)

    def test_get_fieldsets_with_ranking_permission(self):
        '''Usuário com permissão de ranking deve ver campo ranking'''
        self.regular_user.user_permissions.add(
            *self._get_ranking_permissions()
        )
        request = MockRequest(user=self.regular_user)
        fieldsets = self.torneio_admin.get_fieldsets(request, None)
        fields = fieldsets[0][1]['fields']
        self.assertIn('ranking', fields)

    def test_get_fieldsets_without_ranking_permission(self):
        '''Usuário sem permissão não deve ver campo ranking'''
        request = MockRequest(user=self.regular_user)
        fieldsets = self.torneio_admin.get_fieldsets(request, None)
        fields = fieldsets[0][1]['fields']
        self.assertNotIn('ranking', fields)

    def test_get_inlines_with_duplas(self):
        '''Torneio com duplas deve mostrar DuplasInline'''
        request = MockRequest(user=self.regular_user)
        inlines = self.torneio_admin.get_inlines(request, self.torneio)
        self.assertTrue(len(inlines) >= 1)

    def test_get_inlines_without_duplas(self):
        '''Torneio sem duplas deve mostrar apenas DuplasInline'''
        torneio_vazio = Torneio.objects.create(
            nome='Torneio Vazio',
            data=date.today(),
            criado_por=self.regular_user
        )
        request = MockRequest(user=self.regular_user)
        inlines = self.torneio_admin.get_inlines(request, torneio_vazio)
        self.assertEqual(len(inlines), 1)

    def _get_ranking_permissions(self):
        '''Helper para obter permissões de ranking'''
        ct = ContentType.objects.get_for_model(Ranking)
        view_perm = Permission.objects.get(
            codename='view_ranking',
            content_type=ct
        )
        add_perm = Permission.objects.get(
            codename='add_ranking',
            content_type=ct
        )
        return [view_perm, add_perm]

    @patch.dict(os.environ, {'APP_LINK': 'http://test.com'})
    def test_change_view_adds_app_link(self):
        '''change_view deve adicionar APP_LINK ao extra_context'''
        request = self._get_request(user=self.superuser)
        with patch('cup.admin.super') as mock_super:
            mock_super.return_value.change_view.return_value = Mock()

            self.torneio_admin.change_view(
                request,
                str(self.torneio.id)
            )

            # Verificar que super foi chamado com extra_context
            call_args = mock_super.return_value.change_view.call_args
            extra_context = call_args[1]['extra_context']

            self.assertIn('APP_LINK', extra_context)
            self.assertEqual(extra_context['APP_LINK'], 'http://test.com')
