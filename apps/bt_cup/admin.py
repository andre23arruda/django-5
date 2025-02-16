from django.contrib import admin, messages
from django.db.models import Case, When
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Dupla, Torneio, Jogo


@admin.register(Dupla)
class DuplaAdmin(admin.ModelAdmin):
    exclude = ('id', 'criado_por')
    list_display = ('__str__', 'telefone', 'ativo')
    list_editable = ('ativo',)
    search_fields = ('jogador1', 'jogador2', 'ativo')

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
    fields = ('fase', 'dupla_1', 'placar_dupla1', 'x', 'placar_dupla2', 'dupla_2', 'concluido')
    readonly_fields = ('fase', 'dupla_1', 'dupla_2', 'x', 'concluido')
    can_delete = False

    def dupla_1(self, obj):
        if obj.dupla1 is not None:
            if obj.dupla1 == obj.winner:
                trophy = '🏆' if obj.fase == 'FINAL' else ''
                return format_html('<u><strong>{}</strong>{}</u>', obj.dupla1, trophy)
        return obj.dupla1 or '-'
    dupla_1.short_description = 'Dupla 1'

    def dupla_2(self, obj):
        if obj.dupla2 is not None:
            if obj.dupla2 == obj.winner:
                trophy = '🏆' if obj.fase == 'FINAL' else ''
                return format_html('<u><strong>{}</strong></u>{}', obj.dupla2, trophy)
        return obj.dupla2 or '-'
    dupla_2.short_description = 'Dupla 2'

    def has_add_permission(self, request, obj=None):
        return False

    def x(self, obj):
        return 'x'
    x.short_description = ''


class RankingInline(admin.TabularInline):
    model = Torneio.duplas.through
    extra = 0
    fields = ('nome', 'info', 'grupo')
    readonly_fields = ('grupo', 'nome', 'info')
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
                key=lambda q: q.dupla.get_group_data(torneio_obj),
                reverse=True
            )
            pk_list = [q.pk for q in qs_sorted]
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pk_list)])
            qs = qs.order_by(preserved)
        return qs

    def has_add_permission(self, request, obj=None):
        return False

    def nome(self, obj):
        return obj.dupla.__str__()

    def grupo(self, obj):
        return obj.dupla.get_group(obj.torneio).replace('GRUPO ', '') or '-'

    def info(self, obj):
        _, pos, v, p = obj.dupla.get_group_data(obj.torneio)
        result = f'{ -pos } / { v } / { p }'
        if pos == -1 or pos == -2:
            return format_html('<u><strong>{}</strong></u>', result)
        return result
    info.short_description = '#  /  V  /  P'


@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/custom-tabular-inline.css',)}
        js = ['js/create-games-modal.js']

    fieldsets = [
        ('Torneio', {'fields': ('nome', 'data', 'duplas', 'quantidade_grupos', 'ativo')}),
    ]
    change_form_template = 'admin/bt_cup/torneio_change_form.html'
    list_display = ('nome', 'data', 'total_duplas', 'grupos', 'total_jogos', 'ativo')
    autocomplete_fields = ['duplas']
    # filter_horizontal = ['duplas']
    list_filter = ('ativo',)
    inlines = [JogoInline, RankingInline]

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            return super().get_form(request, obj, **kwargs)
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['duplas'].queryset = Dupla.objects.filter(criado_por=request.user).order_by('criado_em')
        return form

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)

    def total_duplas(self, obj):
        return obj.duplas.count()
    total_duplas.short_description = 'Duplas'

    def grupos(self, obj):
        return obj.quantidade_grupos
    grupos.short_description = 'Grupos'

    def total_jogos(self, obj):
        return obj.jogo_set.count()
    total_jogos.short_description = 'Jogos'

    def response_add(self, request, obj, post_url_continue=None):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        response = redirect('admin:bt_cup_torneio_change', obj.id)
        response['location'] += '#jogos-tab'
        return response

    def response_change(self, request, obj):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        response = redirect('admin:bt_cup_torneio_change', obj.id)
        response['location'] += '#jogos-tab'
        return response

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
