import os, re
from django.contrib import admin, messages
from django.db.models import Case, IntegerField, When
from django.shortcuts import redirect
from django.utils.html import format_html
from itertools import zip_longest
from .models import Dupla, Torneio, Jogo


@admin.register(Dupla)
class DuplaAdmin(admin.ModelAdmin):
    fields = ['jogador1', 'jogador2', 'telefone']
    list_display = ['__str__', 'telefone', 'get_torneios']
    search_fields = ['jogador1', 'jogador2']

    def get_torneios(self, obj):
        '''Retorna os torneios em que a dupla participa'''
        return obj.torneio_set.filter(ativo=True).count()
    get_torneios.short_description = 'Torneios'

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
    fields = ['fase', 'dupla_1', 'placar_dupla1', 'x', 'placar_dupla2', 'dupla_2', 'concluido']
    can_delete = False

    def get_queryset(self, request):
        if '/change/' in request.path:
            torneio_id = re.search(r'/([^/]+)/change/', request.path).group(1)
            torneio = Torneio.objects.get(pk=torneio_id)
            queryset = super().get_queryset(request).filter(torneio_id=torneio_id)

            if torneio.quantidade_grupos > 1:
                jogos_grupos = queryset.filter(fase__startswith='GRUPO').values_list('id', 'fase')
                grupos = {'GRUPO 1': [], 'GRUPO 2': [], 'GRUPO 3': [], 'GRUPO 4': []}
                for jogo_id, fase in jogos_grupos:
                    if fase in grupos:
                        grupos[fase].append(jogo_id)

                alternada = []
                for elementos in zip_longest(*grupos.values(), fillvalue=None):
                    alternada.extend([id_jogo for id_jogo in elementos if id_jogo is not None])

                ids_playoff = list(queryset.exclude(fase__startswith='GRUPO').annotate(
                    fase_order=Case(
                        When(fase='OITAVAS', then=1),
                        When(fase='QUARTAS', then=2),
                        When(fase='SEMIFINAIS', then=3),
                        When(fase='TERCEIRO LUGAR', then=4),
                        When(fase='FINAL', then=5),
                        When(fase='CAMPEAO', then=6),
                        default=99,
                        output_field=IntegerField()
                    )
                ).order_by('fase_order', 'id').values_list('id', flat=True))
                alternada.extend(ids_playoff)

                return queryset.filter(id__in=alternada).annotate(
                    custom_order=Case(
                        *[When(id=id_val, then=pos) for pos, id_val in enumerate(alternada)],
                        output_field=IntegerField()
                    )
                ).order_by('custom_order')

        return super().get_queryset(request)

    def get_readonly_fields(self, request, obj=None):
        fields = ['fase', 'dupla_1', 'dupla_2', 'x']
        if not obj.ativo:
            fields += ['placar_dupla1', 'placar_dupla2', 'concluido']
        return fields

    def dupla_1(self, obj):
        if obj.dupla1 is not None:
            if obj.dupla1 == obj.winner:
                trophy = format_html('<span class="mr-2">🏆</span>') if obj.fase == 'FINAL' else ''
                return format_html('''
                    <span style="display: inline-flex; align-items: center;">
                        {}
                        <u style="color: #00a50b"><strong>{}</strong></u>
                    </span>''',
                    trophy,
                    obj.dupla1.render(),
                )
            else:
                return obj.dupla1.render()
        return format_html('<span class="text-muted">A definir</span>')
    dupla_1.short_description = 'Dupla 1'

    def dupla_2(self, obj):
        if obj.dupla2 is not None:
            if obj.dupla2 == obj.winner:
                trophy = format_html('<span class="ml-2">🏆</span>') if obj.fase == 'FINAL' else ''
                return format_html('''
                    <span style="display: inline-flex; align-items: center;">
                        <u style="color: #00a50b"><strong>{}</strong></u>
                        {}
                    </span>''',
                    obj.dupla2.render(),
                    trophy
                )
            else:
                return obj.dupla2.render()
        return format_html('<span class="text-muted">A definir</span>')
    dupla_2.short_description = 'Dupla 2'

    def has_add_permission(self, request, obj=None):
        return False

    def x(self, obj):
        return 'x'
    x.short_description = ''


class JogoOpenInline(admin.TabularInline):
    model = Jogo
    extra = 0
    fields = ['dupla1', 'placar_dupla1', 'x', 'placar_dupla2', 'dupla2', 'obs', 'concluido']
    # raw_id_fields = ('dupla1', 'dupla2')
    readonly_fields = ['x']
    can_delete = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_obj = None

    def get_fields(self, request, obj):
        fields = self.fields
        if request.user.is_superuser:
            return ['fase'] + fields
        return super().get_fields(request, obj)

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['dupla1', 'dupla2'] and self.parent_obj:
            kwargs['queryset'] = self.parent_obj.duplas.all()
        else:
            kwargs['queryset'] = Dupla.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request, obj=None):
        return True

    def x(self, obj):
        return 'x'
    x.short_description = ''


class DuplasInline(admin.TabularInline):
    model = Torneio.duplas.through
    extra = 0
    verbose_name = 'Dupla'

    def dupla_nome(self, obj):
        return obj.dupla
    dupla_nome.short_description = 'Dupla'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['dupla']:
            if request.user.is_superuser:
                kwargs['queryset'] = Dupla.objects.all().order_by('jogador1')
            else:
                kwargs['queryset'] = Dupla.objects.filter(criado_por=request.user).order_by('jogador1')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_fields(self, request, obj):
        if obj.ativo:
            return ['dupla']
        else:
            return ['dupla_nome']

    def get_readonly_fields(self, request, obj=None):
        if obj.ativo:
            return []
        return ['dupla_nome']

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('dupla__jogador1')

    def has_add_permission(self, request, obj=None):
        return obj.ativo

    def has_delete_permission(self, request, obj=None):
        return obj.ativo

    @property
    def verbose_name_plural(self):
        if hasattr(self, 'parent_object') and self.parent_object:
            total = self.parent_object.duplas.count()
            return f'Duplas ({total})'
        return 'Duplas'

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_object = obj
        return super().get_formset(request, obj, **kwargs)

@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': [
            'css/custom-tabular-inline.css',
            'css/hide-related-widgets.css'
        ]}
        js = [
            'js/create-games-modal.js',
            'js/finish-tournament-modal.js',
            'js/hide-phase.js',
            'js/next-stage-modal.js',
            'js/games-counter.js'
        ]

    fieldsets = [
        ('Torneio', {'fields': [
            'nome', 'data', 'quantidade_grupos',
            'playoffs', 'terceiro_lugar', 'open',
            'ativo'
        ]}),
    ]
    change_form_template = 'admin/bt_cup/cup_change_form.html'
    list_display = ['nome', 'data', 'total_duplas', 'grupos', 'total_jogos', 'ativo']
    autocomplete_fields = ['duplas']
    list_filter = ['ativo',]
    search_fields = ['nome']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['APP_LINK'] = os.getenv('APP_LINK')
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def get_inlines(self, request, obj):
        if obj:
            if obj.open and obj.duplas.count() > 0 and obj.ativo:
                return [DuplasInline, JogoOpenInline]
            elif obj.duplas.count() > 0:
                return [DuplasInline, JogoInline]
            else:
                return [DuplasInline]
        return super().get_inlines(request, obj)

    def get_fieldsets(self, request, obj):
        if request.user.is_superuser:
            return [[
                'Torneio', {'fields': [
                    'nome', 'data', 'quantidade_grupos',
                    'playoffs', 'terceiro_lugar', 'open',
                    'ativo', 'criado_por'
                ]}
            ]]
        return super().get_fieldsets(request, obj)

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em']
        return list_display

    # def get_form(self, request, obj=None, **kwargs):
    #     if request.user.is_superuser:
    #         return super().get_form(request, obj, **kwargs)
    #     form = super().get_form(request, obj, **kwargs)
    #     form.base_fields['duplas'].queryset = Dupla.objects.filter(criado_por=request.user).order_by('criado_em')
    #     return form

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
        messages.add_message(request, messages.INFO, 'Torneio criado! Agora adicione as duplas')
        response = redirect('admin:bt_cup_torneio_change', obj.id)
        response['location'] += '#duplas-0-tab'
        return response

    def response_change(self, request, obj):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        response = redirect('admin:bt_cup_torneio_change', obj.id)
        response['location'] += '#jogos-tab'
        return response

    def save_model(self, request, obj, form, change):
        created = not change
        if created and not request.user.is_superuser:
            obj.criado_por = request.user
        # if form.cleaned_data.get('open'):
        #     obj.playoffs = False
        super().save_model(request, obj, form, change)


@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ['css/custom-tabular-inline.css']}

    list_display = ['dupla1', 'placar', 'dupla2', 'concluido', 'fase', 'torneio']
    list_filter = ['fase', 'torneio']
    list_per_page = 15
    ordering = ['-torneio__data']

    def has_module_permission(self, request):
        return request.user.is_superuser