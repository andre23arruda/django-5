from django.contrib import admin, messages
from django.db.models import Case, When
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Jogador, Torneio, Jogo

from django.conf.locale.pt_BR import formats as portuguese
from django.conf.locale.en import formats as english

portuguese.DATE_FORMAT = 'd/m/Y'
portuguese.DATETIME_FORMAT = 'H:i d/m/Y'
english.DATE_FORMAT = 'd/m/Y'
english.DATETIME_FORMAT = 'H:i d/m/Y'


@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):
    exclude = ('criado_por', 'id',)
    list_display = ['nome', 'telefone', 'ativo']
    list_editable = ['ativo']
    list_filter = ['ativo']
    search_fields = ('nome',)

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em']
        return list_display

    def get_search_results(self, request, queryset, search_term):
        '''Sobrescreve os resultados da pesquisa no campo autocomplete.'''
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if '/admin/autocomplete/' in request.path:
            queryset = queryset.filter(ativo=True)
        return queryset, use_distinct

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


class JogoInline(admin.TabularInline):
    model = Jogo
    extra = 0
    fields = ('dupla_1', 'placar_dupla1', 'x', 'placar_dupla2', 'dupla_2', 'quadra', 'concluido')
    readonly_fields = ('dupla_1', 'dupla_2', 'x', 'concluido', 'quadra')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def dupla_1(self, obj):
        if obj.placar_dupla1 is not None and obj.placar_dupla2 is not None:
            if obj.placar_dupla1 > obj.placar_dupla2:
                return format_html('<u><strong>{}</strong></u>', obj.dupla_1())
        return obj.dupla_1()
    dupla_1.short_description = 'Dupla 1'

    def dupla_2(self, obj):
        if obj.placar_dupla1 is not None and obj.placar_dupla2 is not None:
            if obj.placar_dupla2 > obj.placar_dupla1:
                return format_html('<u><strong>{}</strong></u>', obj.dupla_2())
        return obj.dupla_2()
    dupla_2.short_description = 'Dupla 2'

    def x(self, obj):
        return 'x'
    x.short_description = ''


class RankingInline(admin.TabularInline):
    model = Torneio.jogadores.through
    extra = 0
    fields = ('nome', 'pontos')
    readonly_fields = ('nome', 'pontos')
    can_delete = False
    verbose_name = 'Ranking'
    verbose_name_plural = 'Ranking'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        torneio = request.resolver_match.kwargs.get('object_id')

        if torneio:
            qs = qs.filter(torneio=torneio)
            torneio_obj = Torneio.objects.get(pk=torneio)
            qs_sorted = sorted(
                qs,
                key=lambda q: q.jogador.admin_ranking(torneio_obj),
            )
            pk_list = [q.pk for q in qs_sorted]
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pk_list)])
            qs = qs.order_by(preserved)
        return qs

    def has_add_permission(self, request, obj=None):
        return False

    def nome(self, obj):
        return obj.jogador.nome

    def pontos(self, obj):
        vitorias, pontos, saldo = obj.jogador.player_points(obj.torneio)
        return f'{vitorias} / {pontos} / {saldo}'
    pontos.short_description = 'V / P / S'


@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/custom-tabular-inline.css',)}
        js = ['js/create-games-modal.js', 'js/finish-tournament-modal.js']

    fieldsets = [
        ('Torneio', {'fields': ('nome', 'data', 'quadras', 'jogadores', 'ativo')}),
    ]
    change_form_template = 'admin/bt_league/torneio_change_form.html'
    list_display = ['nome', 'data', 'total_jogadores', 'total_jogos', 'ativo']
    autocomplete_fields = ['jogadores']
    list_filter = ('ativo',)
    inlines = [JogoInline, RankingInline]

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em']
        return list_display

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            return super().get_form(request, obj, **kwargs)
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['jogadores'].queryset = Jogador.objects.filter(criado_por=request.user).order_by('nome')
        return form

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)

    def total_jogadores(self, obj):
        return obj.jogadores.count()
    total_jogadores.short_description = 'Jogadores'

    def total_jogos(self, obj):
        return obj.jogo_set.count()
    total_jogos.short_description = 'Jogos'

    def response_add(self, request, obj, post_url_continue=None):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        response = redirect('admin:bt_league_torneio_change', obj.id)
        response['location'] += '#jogos-tab'
        return response

    def response_change(self, request, obj):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        response = redirect('admin:bt_league_torneio_change', obj.id)
        response['location'] += '#jogos-tab'
        return response

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
