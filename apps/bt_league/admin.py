from django.contrib import admin, messages
from django.db.models import Case, When
from django.shortcuts import redirect
from django.urls import path
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
    list_display = ('nome', 'email')


class JogoInline(admin.TabularInline):
    model = Jogo
    extra = 0
    fields = ('dupla_1', 'placar_dupla1', 'x', 'placar_dupla2', 'dupla_2', 'concluido')
    readonly_fields = ('dupla_1', 'dupla_2', 'x')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def dupla_1(self, obj):
        return obj.dupla_1()
    dupla_1.short_description = 'Dupla 1'

    def dupla_2(self, obj):
        return obj.dupla_2()
    dupla_2.short_description = 'Dupla 2'

    def x(self, obj):
        return 'x'
    x.short_description = ''


class RankingInline(admin.TabularInline):
    model = Torneio.jogadores.through
    extra = 0
    fields = ('ranking', 'nome', 'vitorias', 'pontos')
    readonly_fields = ('nome', 'vitorias', 'pontos', 'ranking')
    can_delete = False
    verbose_name = 'Ranking'
    verbose_name_plural = 'Ranking'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        torneio = request.resolver_match.kwargs.get('object_id')

        if torneio:
            torneio_obj = Torneio.objects.get(pk=torneio)
            qs_sorted = sorted(
                qs,
                key=lambda q: q.jogador.player_points(torneio_obj),
                reverse=True
            )
            pk_list = [q.pk for q in qs_sorted]
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pk_list)])
            qs = qs.order_by(preserved)
        return qs

    def has_add_permission(self, request, obj=None):
        return False

    def nome(self, obj):
        return obj.jogador.nome

    def vitorias(self, obj):
        return obj.jogador.player_victories(obj.torneio)
    vitorias.short_description = 'Vitórias'

    def pontos(self, obj):
        return obj.jogador.player_points(obj.torneio)

    def ranking(self, obj):
        return obj.jogador.ranking(obj.torneio)
    ranking.short_description = '#'


@admin.action(description='Gerar jogos')
def create_games(modeladmin, request, queryset):
    for torneio in queryset:
        torneio.create_games()

@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/custom-tabular-inline.css',)}

    fieldsets = [
        # ('', {'fields': ('nome', 'data', 'criado_por'), 'classes': ('',)}),
        ('', {'fields': (('nome', 'ativo'), 'data'), 'classes': ('',)}),
        ('JOGADORES', {'fields': ('jogadores',), 'classes': ('collapse',)}),
    ]
    change_form_template = 'admin/bt_league/torneio_change_form.html'
    list_display = ('nome', 'data', 'total_jogadores', 'total_jogos', 'ativo')
    filter_horizontal = ('jogadores',)
    list_filter = ('ativo',)
    inlines = [JogoInline, RankingInline]
    # actions = [create_games]

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)

    def total_jogadores(self, obj):
        return obj.jogadores.count()
    total_jogadores.short_description = 'Nº Jogadores'

    def total_jogos(self, obj):
        return obj.jogo_set.count()
    total_jogos.short_description = 'Nº Jogos'

    def response_add(self, request, obj, post_url_continue=None):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        return redirect(f'admin:bt_league_torneio_change', obj.id)

    def response_change(self, request, obj):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        return redirect(f'admin:bt_league_torneio_change', obj.id)

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)