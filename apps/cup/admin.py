import os, re
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Dupla, Jogador, Jogo, Ranking, Torneio


class TorneioListFilter(admin.SimpleListFilter):
    title = 'Torneio'
    parameter_name = 'torneio'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            torneios = Torneio.objects.all().order_by('nome')
        else:
            torneios = Torneio.objects.filter(criado_por=request.user).order_by('nome')

        return [(torneio.id, torneio.nome) for torneio in torneios]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(torneio=self.value())
        return queryset


@admin.register(Dupla)
class DuplaAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/cup/admin-dupla.css', 'css/cup/hide-buttons.css')}

    fields = ['jogador1', 'jogador2', 'torneio']
    list_display = ['__str__', 'torneio']
    list_filter = [TorneioListFilter]
    list_per_page = 15
    search_fields = ['jogador1', 'jogador2']

    def get_fields(self, request, obj):
        if request.user.is_superuser:
            return self.fields + ['criado_por', 'ativo']
        return super().get_fields(request, obj)

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em']
        return list_display

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)

    # def has_module_permission(self, request):
    #     return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/cup/hide-buttons.css',)}

    fields = ['nome', 'telefone']
    list_display = ['__str__', 'telefone']
    list_per_page = 15
    search_fields = ['nome']

    def get_fields(self, request, obj):
        if request.user.is_superuser:
            return self.fields + ['criado_por', 'ativo']
        return super().get_fields(request, obj)

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em']
        return list_display

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/cup/hide-buttons.css',)}

    list_display = ['dupla1', 'placar', 'dupla2', 'concluido', 'fase', 'torneio']
    list_filter = ['fase', 'torneio']
    list_per_page = 15
    ordering = ['-torneio__data']

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/cup/hide-buttons.css',)}

    change_form_template = 'admin/cup/ranking_change_form.html'
    fields = ['nome']
    list_display = ['nome', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['APP_LINK'] = os.getenv('APP_LINK')
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def get_fields(self, request, obj):
        if request.user.is_superuser:
            return self.fields + ['criado_por', 'ativo']
        return super().get_fields(request, obj)

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em']
        return list_display

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


class JogosInline(admin.TabularInline):
    model = Jogo
    extra = 0
    fields = ['fase', 'dupla_1', 'pontos_dupla1', 'x', 'pontos_dupla2', 'dupla_2', 'concluido']
    can_delete = False

    def get_queryset(self, request):
        if '/change/' in request.path:
            torneio_id = re.search(r'/([^/]+)/change/', request.path).group(1)
            torneio = Torneio.objects.get(pk=torneio_id)
            queryset = super().get_queryset(request).filter(torneio_id=torneio_id)
            sorted_games = torneio.get_sorted_games(queryset)
            return sorted_games
        return super().get_queryset(request)

    def get_readonly_fields(self, request, obj=None):
        fields = ['fase', 'dupla_1', 'dupla_2', 'x']
        if not obj.ativo:
            fields += ['pontos_dupla1', 'pontos_dupla2', 'concluido']
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


class JogosOpenInline(admin.TabularInline):
    model = Jogo
    extra = 0
    fields = ['dupla1', 'pontos_dupla1', 'x', 'pontos_dupla2', 'dupla2', 'obs', 'concluido']
    readonly_fields = ['x']
    can_delete = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_obj = None

    def get_fields(self, request, obj):
        if request.user.is_superuser:
            return ['fase', 'dupla1', 'pontos_dupla1', 'x', 'pontos_dupla2', 'dupla2', 'obs', 'concluido']
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
    model = Dupla
    extra = 0

    def jogadores(self, obj):
        return obj.__str__()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['jogador1', 'jogador2']:
            if request.user.is_superuser:
                kwargs['queryset'] = Jogador.objects.all().order_by('nome')
            else:
                kwargs['queryset'] = Jogador.objects.filter(criado_por=request.user).order_by('nome')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_exclude(self, request, obj=None):
        exclude_fields = ['id', 'ativo', 'jogador1', 'jogador2', 'criado_por']
        is_active = getattr(obj, 'ativo', False)
        if is_active:
            exclude_fields = ['id', 'ativo', 'criado_por']
            if obj.tipo == 'S':
                exclude_fields.append('jogador2')
        return exclude_fields

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_object = obj
        return super().get_formset(request, obj, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('jogador1__nome')

    def get_readonly_fields(self, request, obj=None):
        is_active = getattr(obj, 'ativo', False)
        if not is_active:
            return ['jogadores']
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        return getattr(obj, 'ativo', False)

    def has_add_permission(self, request, obj=None):
        return getattr(obj, 'ativo', False)

    @property
    def verbose_name(self):
        if hasattr(self, 'parent_object') and self.parent_object:
            if self.parent_object.tipo == 'S':
                return 'Jogador'
        return 'Dupla'

    @property
    def verbose_name_plural(self):
        if hasattr(self, 'parent_object') and self.parent_object:
            total = self.parent_object.duplas.count()
            if self.parent_object.tipo == 'S':
                return f'Jogadores ({total})'
            return f'Duplas ({total})'
        return 'Duplas'


@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/cup/admin-torneio.css', 'css/cup/hide-buttons.css')}
        js = [
            'js/create-games-modal.js',
            'js/finish-tournament-modal.js',
            'js/hide-phase.js',
            'js/next-stage-modal.js',
            'js/games-counter.js'
        ]

    change_form_template = 'admin/cup/cup_change_form.html'
    list_display = ['nome', 'data', 'total_duplas', 'grupos', 'total_jogos', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome']
    fieldsets = [
        ('Torneio', {'fields': [
            'nome', 'data', 'ranking',
            'quantidade_grupos', 'tipo',
            'playoffs', 'terceiro_lugar',
            'open', 'ativo'
        ]}),
    ]

    def total_duplas(self, obj):
        return obj.duplas.count()
    total_duplas.short_description = 'Duplas'

    def grupos(self, obj):
        return obj.quantidade_grupos
    grupos.short_description = 'Grupos'

    def total_jogos(self, obj):
        return obj.jogo_set.count()
    total_jogos.short_description = 'Jogos'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['APP_LINK'] = os.getenv('APP_LINK')
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['ranking']:
            if request.user.is_superuser:
                kwargs['queryset'] = Ranking.objects.all().order_by('nome')
            else:
                kwargs['queryset'] = Ranking.objects.filter(criado_por=request.user).order_by('nome')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_fieldsets(self, request, obj):
        if request.user.is_superuser:
            return [
                ('Torneio', {'fields': [
                    'nome', 'data', 'ranking',
                    'quantidade_grupos', 'tipo',
                    'playoffs', 'terceiro_lugar',
                    'open', 'ativo', 'criado_por'
                ]}),
            ]
        return super().get_fieldsets(request, obj)

    def get_inlines(self, request, obj):
        if obj:
            if obj.open and obj.duplas.count() > 0 and obj.ativo:
                return [DuplasInline, JogosOpenInline]
            elif obj.duplas.count() > 0:
                return [DuplasInline, JogosInline]
            else:
                return [DuplasInline]
        return super().get_inlines(request, obj)

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em']
        return list_display

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)

    def response_add(self, request, obj, post_url_continue=None):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        response = redirect('admin:cup_torneio_change', obj.id)
        tab_param = '#duplas-0-tab'
        if obj.tipo == 'S':
            tab_param = '#jogadores-0-tab'
        response['location'] += tab_param
        return response

    def response_change(self, request, obj):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        response = redirect('admin:cup_torneio_change', obj.id)
        response['location'] += '#jogos-tab'
        return response

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Dupla):
                instance.criado_por = instance.torneio.criado_por
                error = instance.save()
                if error:
                    messages.add_message(request, messages.ERROR, error)
            else:
                instance.save()

        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
