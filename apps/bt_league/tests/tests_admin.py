from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User, Group
from django.urls import reverse
from datetime import date
from unittest.mock import Mock, patch

from bt_league.models import Jogador, Torneio, Jogo, Ranking
from bt_league.admin import (
    JogadorAdmin, TorneioAdmin, JogoAdmin, RankingAdmin,
    JogoInline, RankingInline, JogadoresInline
)


class MockRequest:
    '''Mock de request para testes de admin'''
    def __init__(self, user=None):
        self.user = user
        self.resolver_match = Mock()
        self.resolver_match.kwargs = {}
        self.path = '/admin/'


class JogadorAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()

        # Usuários
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.normal_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='user123',
            is_staff=True
        )
        self.group = Group.objects.create(name='Test Group')
        self.normal_user.groups.add(self.group)

        # Admin
        self.admin = JogadorAdmin(Jogador, self.site)

        # Jogadores
        self.jogador1 = Jogador.objects.create(
            nome='Jogador 1',
            criado_por=self.normal_user,
            grupo_criador=self.group
        )
        self.jogador2 = Jogador.objects.create(
            nome='Jogador 2',
            criado_por=self.superuser
        )

    def test_list_display(self):
        '''Testa campos exibidos na lista'''
        request = MockRequest(self.normal_user)
        list_display = self.admin.get_list_display(request)
        self.assertIn('nome', list_display)
        self.assertIn('telefone', list_display)

    def test_list_display_superuser(self):
        '''Testa campos extras para superuser'''
        request = MockRequest(self.superuser)
        list_display = self.admin.get_list_display(request)
        self.assertIn('criado_por', list_display)
        self.assertIn('criado_em', list_display)
        self.assertIn('grupo_criador', list_display)

    def test_has_delete_permission_superuser(self):
        '''Testa que superuser pode deletar'''
        request = MockRequest(self.superuser)
        self.assertTrue(self.admin.has_delete_permission(request))

    def test_has_delete_permission_normal_user(self):
        '''Testa que usuário normal não pode deletar'''
        request = MockRequest(self.normal_user)
        self.assertFalse(self.admin.has_delete_permission(request))

    def test_get_fields_normal_user(self):
        '''Testa campos para usuário normal'''
        request = MockRequest(self.normal_user)
        fields = self.admin.get_fields(request, self.jogador1)
        self.assertIn('nome', fields)
        self.assertNotIn('criado_por', fields)

    def test_get_fields_superuser(self):
        '''Testa campos extras para superuser'''
        request = MockRequest(self.superuser)
        fields = self.admin.get_fields(request, self.jogador1)
        self.assertIn('nome', fields)
        self.assertIn('criado_por', fields)
        self.assertIn('ativo', fields)

    def test_get_queryset_normal_user(self):
        '''Testa que usuário normal vê apenas seus jogadores'''
        request = MockRequest(self.normal_user)
        queryset = self.admin.get_queryset(request)
        self.assertIn(self.jogador1, queryset)
        self.assertNotIn(self.jogador2, queryset)

    def test_get_queryset_superuser(self):
        '''Testa que superuser vê todos os jogadores'''
        request = MockRequest(self.superuser)
        queryset = self.admin.get_queryset(request)
        self.assertIn(self.jogador1, queryset)
        self.assertIn(self.jogador2, queryset)

    def test_save_model_sets_creator(self):
        '''Testa que criador é definido automaticamente'''
        request = MockRequest(self.normal_user)
        jogador = Jogador(nome='Novo Jogador')
        self.admin.save_model(request, jogador, None, change=False)
        self.assertEqual(jogador.criado_por, self.normal_user)
        self.assertEqual(jogador.grupo_criador, self.group)

    def test_search_results_autocomplete_only_active(self):
        '''Testa que autocomplete retorna apenas jogadores ativos'''
        # Criar jogador inativo
        Jogador.objects.create(
            nome='Jogador Inativo',
            criado_por=self.normal_user,
            ativo=False
        )
        request = MockRequest(self.normal_user)
        request.path = '/admin/autocomplete/'
        queryset = Jogador.objects.all()
        results, _ = self.admin.get_search_results(request, queryset, 'Jogador')

        # Deve retornar apenas jogadores ativos
        self.assertTrue(all(j.ativo for j in results))


class TorneioAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        self.normal_user = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=True
        )
        self.group = Group.objects.create(name='Test Group')
        self.normal_user.groups.add(self.group)
        self.admin = TorneioAdmin(Torneio, self.site)
        self.ranking = Ranking.objects.create(
            nome='Ranking Teste',
            criado_por=self.normal_user
        )
        self.torneio = Torneio.objects.create(
            nome='Torneio Teste',
            data=date(2025, 10, 22),
            criado_por=self.normal_user,
            grupo_criador=self.group,
            ranking=self.ranking
        )

        # Criar jogadores
        self.jogador1 = Jogador.objects.create(
            nome='Jogador 1',
            criado_por=self.normal_user
        )
        self.jogador2 = Jogador.objects.create(
            nome='Jogador 2',
            criado_por=self.normal_user
        )
        self.torneio.jogadores.add(self.jogador1, self.jogador2)

    def test_list_display(self):
        '''Testa campos na lista'''
        request = MockRequest(self.normal_user)
        list_display = self.admin.get_list_display(request)
        self.assertIn('nome', list_display)
        self.assertIn('data', list_display)
        self.assertIn('total_jogadores', list_display)
        self.assertIn('total_jogos', list_display)

    def test_total_jogadores(self):
        '''Testa método total_jogadores'''
        total = self.admin.total_jogadores(self.torneio)
        self.assertEqual(total, 2)

    def test_total_jogos(self):
        '''Testa método total_jogos'''
        # Criar jogos
        Jogo.objects.create(
            torneio=self.torneio,
            dupla1_jogador1=self.jogador1,
            dupla1_jogador2=self.jogador2,
            dupla2_jogador1=self.jogador1,
            dupla2_jogador2=self.jogador2
        )
        total = self.admin.total_jogos(self.torneio)
        self.assertEqual(total, 1)

    def test_has_delete_permission_superuser(self):
        '''Testa permissão de deletar para superuser'''
        request = MockRequest(self.superuser)
        self.assertTrue(self.admin.has_delete_permission(request))

    def test_has_delete_permission_normal_user(self):
        '''Testa que usuário normal não pode deletar'''
        request = MockRequest(self.normal_user)
        self.assertFalse(self.admin.has_delete_permission(request))

    def test_get_queryset_normal_user(self):
        '''Testa queryset para usuário normal'''
        request = MockRequest(self.normal_user)
        queryset = self.admin.get_queryset(request)
        self.assertIn(self.torneio, queryset)

    def test_get_queryset_filters_by_group(self):
        '''Testa que filtra por grupo do usuário'''
        other_user = User.objects.create_user(
            username='other',
            password='other123',
            is_staff=True
        )
        other_torneio = Torneio.objects.create(
            nome='Outro Torneio',
            data=date(2025, 11, 1),
            criado_por=other_user
        )
        request = MockRequest(self.normal_user)
        queryset = self.admin.get_queryset(request)
        self.assertNotIn(other_torneio, queryset)

    def test_save_model_sets_creator(self):
        '''Testa que criador é definido ao salvar'''
        request = MockRequest(self.normal_user)
        torneio = Torneio(
            nome='Novo Torneio',
            data=date(2025, 12, 1)
        )
        self.admin.save_model(request, torneio, None, change=False)
        self.assertEqual(torneio.criado_por, self.normal_user)
        self.assertEqual(torneio.grupo_criador, self.group)

    def test_get_inlines_with_jogadores(self):
        '''Testa inlines quando há jogadores'''
        request = MockRequest(self.normal_user)
        inlines = self.admin.get_inlines(request, self.torneio)
        self.assertEqual(len(inlines), 2)
        self.assertIn(JogadoresInline, inlines)
        self.assertIn(JogoInline, inlines)

    def test_get_inlines_without_jogadores(self):
        '''Testa inlines quando não há jogadores'''
        torneio_vazio = Torneio.objects.create(
            nome='Torneio Vazio',
            data=date(2025, 12, 1),
            criado_por=self.normal_user
        )
        request = MockRequest(self.normal_user)
        inlines = self.admin.get_inlines(request, torneio_vazio)
        self.assertEqual(len(inlines), 1)
        self.assertIn(JogadoresInline, inlines)

    def test_formfield_for_foreignkey_filters_ranking(self):
        '''Testa que filtro de ranking funciona'''
        other_ranking = Ranking.objects.create(
            nome='Outro Ranking',
            criado_por=self.superuser
        )
        request = MockRequest(self.normal_user)
        db_field = Torneio._meta.get_field('ranking')
        formfield = self.admin.formfield_for_foreignkey(db_field, request)

        # Usuário normal deve ver apenas seu ranking
        self.assertIn(self.ranking, formfield.queryset)
        self.assertNotIn(other_ranking, formfield.queryset)

    # @patch.dict('os.environ', {'APP_LINK': 'http://testserver'})
    # def test_change_view_adds_app_link(self):
    #     '''Testa que change_view adiciona APP_LINK ao contexto'''
    #     request = MockRequest(self.superuser)
    #     with patch.object(TorneioAdmin, 'change_view', wraps=self.admin.change_view) as mock_method:
    #         # Simular chamada
    #         extra_context = {}
    #         result = self.admin.change_view(request, str(self.torneio.id), '', extra_context)
    #         self.assertIn('APP_LINK', extra_context)


class JogoAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        self.normal_user = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=True
        )
        self.admin = JogoAdmin(Jogo, self.site)
        self.torneio = Torneio.objects.create(
            nome='Torneio',
            data=date(2025, 10, 22),
            criado_por=self.normal_user
        )
        self.jogador1 = Jogador.objects.create(
            nome='J1',
            criado_por=self.normal_user
        )
        self.jogador2 = Jogador.objects.create(
            nome='J2',
            criado_por=self.normal_user
        )
        self.jogador3 = Jogador.objects.create(
            nome='J3',
            criado_por=self.normal_user
        )
        self.jogador4 = Jogador.objects.create(
            nome='J4',
            criado_por=self.normal_user
        )
        self.jogo = Jogo.objects.create(
            torneio=self.torneio,
            dupla1_jogador1=self.jogador1,
            dupla1_jogador2=self.jogador2,
            dupla2_jogador1=self.jogador3,
            dupla2_jogador2=self.jogador4
        )

    def test_has_module_permission_superuser(self):
        '''Testa que apenas superuser tem acesso ao módulo'''
        request = MockRequest(self.superuser)
        self.assertTrue(self.admin.has_module_permission(request))

    def test_has_module_permission_normal_user(self):
        '''Testa que usuário normal não tem acesso ao módulo'''
        request = MockRequest(self.normal_user)
        self.assertFalse(self.admin.has_module_permission(request))

    def test_list_display(self):
        '''Testa campos na lista'''
        self.assertIn('__str__', self.admin.list_display)
        self.assertIn('torneio', self.admin.list_display)
        self.assertIn('concluido', self.admin.list_display)


class RankingAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        self.normal_user = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=True
        )
        self.group = Group.objects.create(name='Test Group')
        self.normal_user.groups.add(self.group)
        self.admin = RankingAdmin(Ranking, self.site)
        self.ranking1 = Ranking.objects.create(
            nome='Ranking 1',
            criado_por=self.normal_user,
            grupo_criador=self.group
        )
        self.ranking2 = Ranking.objects.create(
            nome='Ranking 2',
            criado_por=self.superuser
        )

    def test_list_display(self):
        '''Testa campos na lista'''
        self.assertIn('nome', self.admin.list_display)
        self.assertIn('ativo', self.admin.list_display)

    def test_get_queryset_normal_user(self):
        '''Testa queryset para usuário normal'''
        request = MockRequest(self.normal_user)
        queryset = self.admin.get_queryset(request)
        self.assertIn(self.ranking1, queryset)
        self.assertNotIn(self.ranking2, queryset)

    def test_get_queryset_superuser(self):
        '''Testa queryset para superuser'''
        request = MockRequest(self.superuser)
        queryset = self.admin.get_queryset(request)
        self.assertIn(self.ranking1, queryset)
        self.assertIn(self.ranking2, queryset)

    def test_save_model_sets_creator(self):
        '''Testa que criador é definido'''
        request = MockRequest(self.normal_user)
        ranking = Ranking(nome='Novo Ranking')
        self.admin.save_model(request, ranking, None, change=False)
        self.assertEqual(ranking.criado_por, self.normal_user)
        self.assertEqual(ranking.grupo_criador, self.group)


class JogoInlineTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.user = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=True
        )
        self.torneio_ativo = Torneio.objects.create(
            nome='Torneio Ativo',
            data=date(2025, 10, 22),
            criado_por=self.user,
            ativo=True
        )
        self.torneio_inativo = Torneio.objects.create(
            nome='Torneio Inativo',
            data=date(2025, 10, 22),
            criado_por=self.user,
            ativo=False
        )
        self.jogador1 = Jogador.objects.create(
            nome='J1',
            criado_por=self.user
        )
        self.jogador2 = Jogador.objects.create(
            nome='J2',
            criado_por=self.user
        )
        self.jogador3 = Jogador.objects.create(
            nome='J3',
            criado_por=self.user
        )
        self.jogador4 = Jogador.objects.create(
            nome='J4',
            criado_por=self.user
        )
        self.jogo = Jogo.objects.create(
            torneio=self.torneio_ativo,
            dupla1_jogador1=self.jogador1,
            dupla1_jogador2=self.jogador2,
            dupla2_jogador1=self.jogador3,
            dupla2_jogador2=self.jogador4,
            placar_dupla1=10,
            placar_dupla2=6
        )
        self.inline = JogoInline(Torneio, self.site)

    def test_dupla_1_winner_formatting(self):
        '''Testa formatação da dupla vencedora'''
        result = self.inline.dupla_1(self.jogo)

        # Deve conter tags HTML de formatação para vencedor
        self.assertIn('<u', result)
        self.assertIn('color: #00a50b', result)

    def test_dupla_2_loser_formatting(self):
        '''Testa formatação da dupla perdedora'''
        result = self.inline.dupla_2(self.jogo)

        # Não deve ter formatação especial
        self.assertNotIn('<u', result)

    def test_readonly_fields_torneio_ativo(self):
        '''Testa campos readonly quando torneio está ativo'''
        request = MockRequest(self.user)
        readonly = self.inline.get_readonly_fields(request, self.torneio_ativo)
        self.assertIn('dupla_1', readonly)
        self.assertIn('dupla_2', readonly)
        self.assertNotIn('placar_dupla1', readonly)

    def test_readonly_fields_torneio_inativo(self):
        '''Testa campos readonly quando torneio está inativo'''
        request = MockRequest(self.user)
        readonly = self.inline.get_readonly_fields(request, self.torneio_inativo)
        self.assertIn('placar_dupla1', readonly)
        self.assertIn('placar_dupla2', readonly)
        self.assertIn('concluido', readonly)

    def test_has_add_permission(self):
        '''Testa que não é possível adicionar jogos pelo inline'''
        request = MockRequest(self.user)
        self.assertFalse(self.inline.has_add_permission(request))


class JogadoresInlineTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.user = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        self.torneio_ativo = Torneio.objects.create(
            nome='Torneio Ativo',
            data=date(2025, 10, 22),
            criado_por=self.user,
            ativo=True
        )
        self.torneio_inativo = Torneio.objects.create(
            nome='Torneio Inativo',
            data=date(2025, 10, 22),
            criado_por=self.user,
            ativo=False
        )
        self.jogador1 = Jogador.objects.create(
            nome='J1',
            criado_por=self.user
        )
        self.jogador2 = Jogador.objects.create(
            nome='J2',
            criado_por=self.superuser
        )
        self.inline = JogadoresInline(Torneio, self.site)

    def test_has_add_permission_torneio_ativo(self):
        '''Testa que pode adicionar jogadores em torneio ativo'''
        request = MockRequest(self.user)
        self.assertTrue(self.inline.has_add_permission(request, self.torneio_ativo))

    def test_has_add_permission_torneio_inativo(self):
        '''Testa que não pode adicionar jogadores em torneio inativo'''
        request = MockRequest(self.user)
        self.assertFalse(self.inline.has_add_permission(request, self.torneio_inativo))

    def test_has_delete_permission_torneio_ativo(self):
        '''Testa que pode remover jogadores de torneio ativo'''
        request = MockRequest(self.user)
        self.assertTrue(self.inline.has_delete_permission(request, self.torneio_ativo))

    def test_has_delete_permission_torneio_inativo(self):
        '''Testa que não pode remover jogadores de torneio inativo'''
        request = MockRequest(self.user)
        self.assertFalse(self.inline.has_delete_permission(request, self.torneio_inativo))

    def test_formfield_filters_jogadores_normal_user(self):
        '''Testa que usuário normal vê apenas seus jogadores'''
        request = MockRequest(self.user)
        db_field = Torneio.jogadores.through._meta.get_field('jogador')
        formfield = self.inline.formfield_for_foreignkey(db_field, request)
        self.assertIn(self.jogador1, formfield.queryset)
        self.assertNotIn(self.jogador2, formfield.queryset)

    def test_formfield_filters_jogadores_superuser(self):
        '''Testa que superuser vê todos os jogadores'''
        request = MockRequest(self.superuser)
        db_field = Torneio.jogadores.through._meta.get_field('jogador')
        formfield = self.inline.formfield_for_foreignkey(db_field, request)
        self.assertIn(self.jogador1, formfield.queryset)
        self.assertIn(self.jogador2, formfield.queryset)


class AdminIntegrationTest(TestCase):
    '''Testes de integração do admin'''

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.client.force_login(self.superuser)
        self.user = User.objects.create_user(
            username='user',
            password='user123',
            is_staff=True
        )
        self.jogador = Jogador.objects.create(
            nome='Jogador Teste',
            criado_por=self.user
        )

    def test_jogador_admin_changelist(self):
        '''Testa listagem de jogadores no admin'''
        url = reverse('admin:bt_league_jogador_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jogador Teste')

    def test_jogador_admin_add(self):
        '''Testa adição de jogador'''
        url = reverse('admin:bt_league_jogador_add')
        self.client.post(url, {
            'nome': 'Novo Jogador',
            'email': 'novo@test.com',
            'telefone': '11999999999',
            'criado_por': self.superuser.id
        })
        self.assertEqual(Jogador.objects.filter(nome='Novo Jogador').count(), 1)

    def test_jogador_not_created_if_criado_por_is_none(self):
        url = reverse('admin:bt_league_jogador_add')
        self.client.post(url, {
            'nome': 'Novo Jogador None',
            'email': 'novo@test.com',
            'telefone': '11999999999',
            'criado_por': ''
        })
        # Jogador não deve ser criado
        self.assertEqual(Jogador.objects.filter(nome='Novo Jogador None').count(), 0)

    def test_jogador_admin_change(self):
        '''Testa edição de jogador'''
        url = reverse('admin:bt_league_jogador_change', args=[self.jogador.id])
        response = self.client.post(url, {
            'nome': 'Jogador Teste Atualizado',
            'email': 'novo@test.com',
            'telefone': '11999999999',
            'criado_por': self.superuser.id
        })
        self.assertEqual(response.status_code, 302)

        # Jogador deve ser atualizado
        jogador_atualizado = Jogador.objects.get(nome='Jogador Teste Atualizado')
        self.assertEqual(jogador_atualizado.id, self.jogador.id)

    def test_torneio_admin_changelist(self):
        '''Testa listagem de torneios'''
        url = reverse('admin:bt_league_torneio_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_ranking_admin_changelist(self):
        '''Testa listagem de rankings'''
        url = reverse('admin:bt_league_ranking_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)