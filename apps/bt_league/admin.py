import os, re
from django import forms
from django.conf.locale.pt_BR import formats as portuguese
from django.conf.locale.en import formats as english
from django.contrib import admin, messages
from django.db.models import Case, Q, When
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from utils.send_email import send_telegram_msg
from .models import Jogador, Jogo, Ranking, Torneio

portuguese.DATE_FORMAT = 'd/m/Y'
portuguese.DATETIME_FORMAT = 'H:i d/m/Y'
english.DATE_FORMAT = 'd/m/Y'
english.DATETIME_FORMAT = 'H:i d/m/Y'


@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ['css/cup/hide-buttons.css']}

    fields = ['nome', 'telefone', 'email']
    list_display = ['nome', 'telefone']
    search_fields = ['nome']

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        through_model = Torneio.jogadores.through
        jogador_ids = [obj.id for obj in objs]
        relacoes = through_model.objects.filter(
            jogador_id__in=jogador_ids
        ).select_related('torneio')
        relacoes_dict = {rel.id: str(rel.torneio) for rel in relacoes}

        def process_items(items):
            processed = []
            for item in items:
                if isinstance(item, list):
                    processed.append(process_items(item))
                else:
                    item_str = str(item)
                    if 'Torneio_jogadores object' in item_str:
                        match = re.search(r'Torneio_jogadores object \((\d+)\)', item_str)
                        if match:
                            relacao_id = int(match.group(1))
                            torneio_nome = relacoes_dict.get(relacao_id, 'Torneio')
                            item_str = item_str.replace(
                                f'Relacionamento torneio-jogador: Torneio_jogadores object ({relacao_id})',
                                f'Inscrição no torneio: {torneio_nome}'
                            )
                    processed.append(item_str)
            return processed

        deleted_objects_modified = process_items(deleted_objects)
        model_count_modified = {}
        for key, value in model_count.items():
            if 'torneio-jogador' in key.lower() or 'torneio_jogadores' in key.lower():
                model_count_modified['Incrições'] = value
            else:
                model_count_modified[key] = value
        return deleted_objects_modified, model_count_modified, perms_needed, protected

    def get_fields(self, request, obj):
        if request.user.is_superuser:
            return self.fields + ['criado_por', 'grupo_criador', 'ativo']
        return super().get_fields(request, obj)

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em', 'grupo_criador']
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
        user_group = request.user.groups.first()
        if user_group:
            return super().get_queryset(request).filter(Q(criado_por=request.user) | Q(grupo_criador=user_group))
        return super().get_queryset(request).filter(Q(criado_por=request.user))

    def save_model(self, request, obj, form, change):
        created = not change
        if created and not request.user.is_superuser:
            obj.criado_por = request.user
            obj.grupo_criador = request.user.groups.first()
        super().save_model(request, obj, form, change)


class JogoInline(admin.TabularInline):
    model = Jogo
    extra = 0
    fields = ['quadra', 'dupla_1', 'placar_dupla1', 'x', 'placar_dupla2', 'dupla_2', 'concluido']
    can_delete = False

    def get_readonly_fields(self, request, obj=None):
        fields = ['dupla_1', 'dupla_2', 'x', 'quadra']
        if not obj.ativo:
            fields += ['placar_dupla1', 'placar_dupla2', 'concluido']
        return fields

    def has_add_permission(self, request, obj=None):
        return False

    def dupla_1(self, obj):
        if obj.placar_dupla1 is not None and obj.placar_dupla2 is not None:
            if obj.placar_dupla1 > obj.placar_dupla2:
                return format_html('<u style="color: #00a50b"><strong>{}</strong></u>', obj.dupla_1())
        return obj.dupla_1()
    dupla_1.short_description = 'Dupla 1'

    def dupla_2(self, obj):
        if obj.placar_dupla1 is not None and obj.placar_dupla2 is not None:
            if obj.placar_dupla2 > obj.placar_dupla1:
                return format_html('<u style="color: #00a50b"><strong>{}</strong></u>', obj.dupla_2())
        return obj.dupla_2()
    dupla_2.short_description = 'Dupla 2'

    def x(self, obj):
        return 'x'
    x.short_description = ''


class RankingInline(admin.TabularInline):
    model = Torneio.jogadores.through
    extra = 0
    fields = ['nome', 'pontos']
    readonly_fields = ['nome', 'pontos']
    can_delete = False
    verbose_name = 'Jogadores'
    verbose_name_plural = 'Jogadores'

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
        vitorias, pontos, saldo, jogos = obj.jogador.player_points(obj.torneio)
        return f'{vitorias} / {pontos} / {saldo}'
    pontos.short_description = 'V / P / S'


class JogadoresInline(admin.TabularInline):
    model = Torneio.jogadores.through
    extra = 0
    verbose_name = 'Jogador'

    def jogador_nome(self, obj):
        return obj.jogador.nome
    jogador_nome.short_description = 'Jogador'

    def get_fields(self, request, obj):
        if obj.ativo:
            return ['jogador']
        else:
            return ['jogador_nome']

    def get_readonly_fields(self, request, obj=None):
        if obj.ativo:
            return []
        return ['jogador_nome']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['jogador']:
            if request.user.is_superuser:
                kwargs['queryset'] = Jogador.objects.all().order_by('nome')
            else:
                kwargs['queryset'] = Jogador.objects.filter(criado_por=request.user).order_by('nome')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request, obj=None):
        return obj.ativo

    def has_delete_permission(self, request, obj=None):
        return obj.ativo

    @property
    def verbose_name_plural(self):
        if hasattr(self, 'parent_object') and self.parent_object:
            total = self.parent_object.jogadores.count()
            return f'Jogadores ({total})'
        return 'Jogadores'

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_object = obj
        return super().get_formset(request, obj, **kwargs)


class TorneioAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['ranking'].widget.can_change_related = False
        # self.fields['ranking'].widget.can_delete_related = False
        # self.fields['ranking'].widget.can_view_related = False

    class Meta:
        model = Torneio
        fields = '__all__'


@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ['css/league/admin-torneio.css']}
        js = [
            'js/create-games-modal.js',
            'js/finish-tournament-modal.js',
            'js/hide-phase.js',
            'js/games-counter.js',
            'js/players-inline-text.js',
        ]

    fieldsets = [
        ['Torneio', {'fields': ['nome', 'data', 'quadras', 'ativo']}],
    ]
    change_form_template = 'admin/bt_league/league_change_form.html'
    list_display = ['nome', 'data', 'total_jogadores', 'total_jogos', 'ativo']
    # autocomplete_fields = ['jogadores']
    list_filter = ['ativo']
    search_fields = ['nome']
    form = TorneioAdminForm

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['APP_LINK'] = os.getenv('APP_LINK')
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        through_model = Torneio.jogadores.through
        torneio_ids = [obj.id for obj in objs]
        relacoes = through_model.objects.filter(
            torneio_id__in=torneio_ids
        ).select_related('jogador')
        relacoes_dict = {rel.id: str(rel.jogador) for rel in relacoes}

        def process_items(items):
            processed = []
            for item in items:
                if isinstance(item, list):
                    processed.append(process_items(item))
                else:
                    item_str = str(item)
                    if 'Torneio_jogadores object' in item_str:
                        match = re.search(r'Torneio_jogadores object \((\d+)\)', item_str)
                        if match:
                            relacao_id = int(match.group(1))
                            jogador_nome = relacoes_dict.get(relacao_id, 'Jogador')
                            item_str = item_str.replace(
                                f'Relacionamento torneio-jogador: Torneio_jogadores object ({relacao_id})',
                                f'Incrição jogador: {jogador_nome}'
                            )
                    processed.append(item_str)
            return processed

        deleted_objects_modified = process_items(deleted_objects)
        model_count_modified = {}
        for key, value in model_count.items():
            if 'torneio-jogador' in key.lower() or 'torneio_jogadores' in key.lower():
                model_count_modified['Incrições'] = value
            else:
                model_count_modified[key] = value
        return deleted_objects_modified, model_count_modified, perms_needed, protected

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['ranking']:
            if request.user.is_superuser:
                kwargs['queryset'] = Ranking.objects.all().order_by('nome')
            else:
                kwargs['queryset'] = Ranking.objects.filter(criado_por=request.user).order_by('nome')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_inlines(self, request, obj):
        if obj:
            if obj.jogadores.count() > 0:
                return [JogadoresInline, JogoInline]
            else:
                return [JogadoresInline]
        return super().get_inlines(request, obj)

    def get_fieldsets(self, request, obj):
        has_ranking_view_perm = request.user.has_perm('bt_league.view_ranking')
        has_ranking_add_perm = request.user.has_perm('bt_league.add_ranking')
        base_fields = ['nome', 'data', 'quadras', 'ativo']
        if has_ranking_view_perm and has_ranking_add_perm:
            base_fields.insert(2, 'ranking')
        if request.user.is_superuser:
            base_fields.extend(['criado_por', 'grupo_criador'])
        return [['Torneio', {'fields': base_fields}]]

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em', 'grupo_criador']
        return list_display

    # def get_form(self, request, obj=None, **kwargs):
    #     if request.user.is_superuser:
    #         return super().get_form(request, obj, **kwargs)
    #     form = super().get_form(request, obj, **kwargs)
    #     user_group = request.user.groups.first()
    #     if user_group:
    #         form.base_fields['jogadores'].queryset = Jogador.objects.filter(Q(criado_por=request.user) | Q(grupo_criador=user_group)).order_by('nome')
    #     else:
    #         form.base_fields['jogadores'].queryset = Jogador.objects.filter(criado_por=request.user).order_by('nome')
    #     return form

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        user_group = request.user.groups.first()
        if user_group:
            return super().get_queryset(request).filter(Q(criado_por=request.user) | Q(grupo_criador=user_group))
        return super().get_queryset(request).filter(criado_por=request.user)

    def total_jogadores(self, obj):
        return obj.jogadores.count()
    total_jogadores.short_description = 'Jogadores'

    def total_jogos(self, obj):
        return obj.jogo_set.count()
    total_jogos.short_description = 'Jogos'

    def response_add(self, request, obj, post_url_continue=None):
        messages.add_message(request, messages.INFO, 'Torneio criado! Agora adicione os jogadores')
        response = redirect('admin:bt_league_torneio_change', obj.id)
        response['location'] += '#jogadores-0-tab'
        return response

    def response_change(self, request, obj):
        messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        response = redirect('admin:bt_league_torneio_change', obj.id)
        response['location'] += '#jogos-tab'
        return response

    def save_model(self, request, obj, form, change):
        created = not change
        if created and not request.user.is_superuser:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
        if created:
            url = f'{os.getenv("HOST_ADDRESS")}{reverse("admin:bt_league_torneio_change", args=[obj.id])}'
            send_telegram_msg(obj, url)
            # send_email_html(
            #     title='Torneio criado com sucesso',
            #     msg_html=f'''
            #         <h2>O torneio <u>"{obj.nome}"</u> foi pelo usuário <u>{obj.criado_por}</u>!</h2>
            #         <br>
            #         <h3>Data de criação: {obj.criado_em.strftime('%H:%M - %d/%m/%Y')}</h3>
            #         <br>
            #         <h3>Acesse através <a href="{url}">desse link</a></h3>
            #         <br>
            #         <p>Att, Pódio Digital</p>
            #     '''
            # )


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    change_form_template = 'admin/bt_league/ranking_change_form.html'
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
            return self.fields + ['criado_por', 'grupo_criador']
        return super().get_fields(request, obj)

    def get_list_display(self, request):
        list_display = self.list_display
        if request.user.is_superuser:
            return list_display + ['criado_por', 'criado_em', 'grupo_criador']
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
        user_group = request.user.groups.first()
        if user_group:
            return super().get_queryset(request).filter(Q(criado_por=request.user) | Q(grupo_criador=user_group))
        return super().get_queryset(request).filter(criado_por=request.user)

    def save_model(self, request, obj, form, change):
        created = not change
        if created and not request.user.is_superuser:
            obj.criado_por = request.user
            obj.grupo_criador = request.user.groups.first()
        super().save_model(request, obj, form, change)


@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ['css/custom-tabular-inline.css']}

    fields = [
        'torneio',
        'quadra',
        'dupla1_jogador1',
        'dupla1_jogador2',
        'placar_dupla1',
        'dupla2_jogador1',
        'dupla2_jogador2',
        'placar_dupla2',
        'concluido',
    ]

    list_display = ['__str__', 'torneio', 'concluido']
    list_filter = ['torneio']
    list_per_page = 15
    ordering = ['-torneio__data']

    def has_module_permission(self, request):
        return request.user.is_superuser