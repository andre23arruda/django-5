import os, re
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Prefetch, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from utils.send_email import send_telegram_msg
from .models import Dupla, Jogador, Jogo, Torneio


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
        css = {'all': ['css/cup/admin-dupla.css', 'css/cup/hide-buttons.css']}

    fields = ['torneio', 'jogador1', 'jogador2']
    list_display = ['__str__', 'torneio']
    list_filter = [TorneioListFilter]
    list_per_page = 15
    readonly_fields = ['torneio']
    search_fields = ['jogador1', 'jogador2']

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['jogador1', 'jogador2']:
            if request.user.is_superuser:
                kwargs['queryset'] = Jogador.objects.all().order_by('nome')
            else:
                kwargs['queryset'] = Jogador.objects.filter(criado_por=request.user).order_by('nome')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
        if created and not request.user.is_superuser:
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

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

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
        if created and not request.user.is_superuser:
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

    def get_fields(self, request, obj):
        if obj.ativo:
            return self.fields + ['obs_icon']
        return super().get_fields(request, obj)

    def get_readonly_fields(self, request, obj=None):
        fields = ['fase', 'dupla_1', 'dupla_2', 'x', 'obs_icon']
        if not obj.ativo:
            fields += ['pontos_dupla1', 'pontos_dupla2', 'concluido']
        return fields

    def dupla_1(self, obj):
        if obj.dupla1 is not None:
            if obj.dupla1 == obj.winner:
                return format_html('''
                    <span style="display: inline-flex; align-items: center;">
                        <u style="color: #00a50b"><strong>{}</strong></u>
                    </span>''',
                    obj.dupla1.render(),
                )
            else:
                return obj.dupla1.render()

        help_text = obj.help_text(0)
        if help_text:
            return format_html('<span class="text-muted">{}</span>', help_text)

        return format_html('<span class="text-muted">A definir</span>')
    dupla_1.short_description = 'Dupla 1'

    def dupla_2(self, obj):
        if obj.dupla2 is not None:
            if obj.dupla2 == obj.winner:
                return format_html('''
                    <span style="display: inline-flex; align-items: center;">
                        <u style="color: #00a50b"><strong>{}</strong></u>
                    </span>''',
                    obj.dupla2.render(),
                )
            else:
                return obj.dupla2.render()

        help_text = obj.help_text(1)
        if help_text:
            return format_html('<span class="text-muted">{}</span>', help_text)
        
        return format_html('<span class="text-muted">A definir</span>')
    dupla_2.short_description = 'Dupla 2'

    def obs_icon(self, obj):
        '''Campo com ícone para abrir modal de observações'''
        if obj.pk:
            has_obs = 'has-obs' if obj.obs else ''
            obs_text = obj.obs or ''
            return format_html('''
                <button
                    type="button"
                    class="btn obs-modal-btn {} text-white"
                    data-jogo-id="{}"
                    data-obs="{}"
                    title="{}"
                >
                    💬
                </button>''',
                has_obs,
                obj.pk,
                obs_text.replace('"', '&quot;'),
                obj.obs or 'Adicionar observação'
            )
        return '-'
    obs_icon.short_description = 'Obs'

    def has_add_permission(self, request, obj=None):
        return False

    def x(self, obj):
        return 'x'
    x.short_description = ''


class DuplasInline(admin.TabularInline):
    model = Dupla
    can_delete = False
    can_add = False

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            return obj.quantidade_times - len(obj.duplas.all())
        return 0

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
        fields = super().get_readonly_fields(request, obj)
        return list(fields) 

    @property
    def verbose_name(self):
        if hasattr(self, 'parent_object') and self.parent_object:
            if self.parent_object.tipo == 'S':
                return 'Jogador'
        return 'Dupla'

    @property
    def verbose_name_plural(self):
        if hasattr(self, 'parent_object') and self.parent_object:
            if self.parent_object.tipo == 'S':
                return f'Jogadores'
        return 'Duplas'


@admin.register(Torneio)
class TorneioAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': [
            'css/cup/admin-torneio.css',
            'css/futevolei/admin-torneio.css',
            'css/cup/hide-buttons.css',
            'css/cup/obs-modal.css',
            'css/save-game.css',
        ]}
        js = [
            'js/create-games-modal.js',
            'js/finish-tournament-modal.js',
            'js/hide-phase.js',
            'js/next-stage-modal.js',
            'js/games-counter.js',
            'js/teams-inline-text.js',
            'js/futevolei/obs-modal.js',
            'js/futevolei/save-game.js',
        ]

    change_form_template = 'admin/futevolei/futevolei_change_form.html'
    date_hierarchy = 'data'
    list_display = ['nome', 'data', 'tipo', 'total_jogos', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome']
    fieldsets = [
        ('Torneio', {'fields': [
            'nome', 'data', 'quantidade_times',
            'tipo', 'draw_pairs','ativo',
            'inscricao_aberta'
        ]}),
    ]

    def total_jogos(self, obj):
        return obj.jogo_set.count()
    total_jogos.short_description = 'Jogos'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['APP_LINK'] = os.getenv('APP_LINK')
        extra_context['sheet_perm'] =  request.user.has_perm('features.view_podiodigitalfeatureplanilha')
        # extra_context['sheet_perm'] = (
        #     request.user.is_superuser or
        #     request.user.groups.filter(name='pd-feature-sheet').exists()
        # )
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def get_fieldsets(self, request, obj):
        has_link_perm = request.user.has_perm('features.view_podiodigitalfeaturelink')
        base_fields = [
            'nome', 'data', 'quantidade_times',
            'tipo', 'draw_pairs', 'ativo',
        ]
        if has_link_perm:
            base_fields.insert(-1, 'inscricao_aberta')
        if request.user.is_superuser:
            base_fields.extend(['criado_por'])
        return [['Torneio', {'fields': base_fields}]]

    def get_inlines(self, request, obj):
        if obj:
            if obj.duplas.filter(jogador1=None).exists() or obj.duplas.filter(jogador2=None).exists():
                return [DuplasInline]
            elif obj.duplas.count() == obj.quantidade_times:
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
        response = redirect('admin:futevolei_torneio_change', obj.id)
        tab_param = '#duplas-tab'
        if obj.tipo == 'S':
            tab_param = '#jogadores-tab'
        response['location'] += tab_param
        return response

    def response_change(self, request, obj):
        storage = messages.get_messages(request)
        warning = False
        for msg in storage:
            if msg.level_tag == 'warning':
                warning = True
                break
        storage.used = False

        response = redirect('admin:futevolei_torneio_change', obj.id)
        if not warning:
            response['location'] += '#jogos-tab'
            messages.add_message(request, messages.INFO, 'Informações salvas com sucesso.')
        else:
            response['location'] += f'#duplas-tab'

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

        if formset.model == Dupla:
            duplas = form.instance.duplas.all()
            if duplas.filter(jogador1=None).exists() or duplas.filter(jogador2=None).exists():
                messages.warning(request, 'Atenção: Há duplas sem jogadores cadastradas neste torneio!')
            elif form.instance.duplas.count() != form.instance.quantidade_times:
                messages.warning(request, 'Atenção: O número de duplas cadastradas deve ser igual à quantidade de times definida para o torneio!')

    def save_model(self, request, obj, form, change):
        created = not change
        if created and not request.user.is_superuser:
            obj.criado_por = request.user

        jogadores = []
        total_duplas = int(request.POST.get('duplas-TOTAL_FORMS', 0))
        for i in range(total_duplas):
            if request.POST.get(f'duplas-{i}-DELETE') == 'on':
                continue
            j1 = request.POST.get(f'duplas-{i}-jogador1')
            j2 = request.POST.get(f'duplas-{i}-jogador2')
            if j1:
                jogadores.append(j1)
            if j2:
                jogadores.append(j2)

        if len(jogadores) != len(set(jogadores)):
            messages.warning(request, 'Atenção: Há jogadores repetidos cadastrados nas duplas deste torneio!')

        # if change and 'quantidade_times' in form.changed_data and obj.has_games():
        #     messages.warning(request, 'A quantidade de times foi modificada. Você precisa gerar os jogos deste torneio novamente!')

        super().save_model(request, obj, form, change)
        if created:
            url = f'{os.getenv("APP_LINK")}{reverse("admin:futevolei_torneio_change", args=[obj.id])}'
            if not settings.DEBUG:
                send_telegram_msg(obj, url)
        if len(obj.duplas.all()) >= obj.quantidade_times:
            duplas = obj.duplas.all()
            for i in range(obj.quantidade_times, len(duplas)):
                duplas[i].delete()


