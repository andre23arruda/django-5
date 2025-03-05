from django.contrib import admin
from django.conf.locale.pt_BR import formats as portuguese
from django.conf.locale.en import formats as english
from django.utils import timezone

from .models import (
    FeriadoPontoFacultativo,
    Escala,
    OrdemPlantonista,
    Plantao,
    Plantonista
)

portuguese.DATE_FORMAT = 'd/m/Y'
portuguese.DATETIME_FORMAT = 'H:i d/m/Y'
english.DATE_FORMAT = 'd/m/Y'
english.DATETIME_FORMAT = 'H:i d/m/Y'


@admin.register(Plantao)
class PlantaoAdmin(admin.ModelAdmin):
    list_display = ('plantonista', 'data', 'turno')
    list_filter = ('data', 'escala')
    ordering = ('-data',)
    list_per_page = 31

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)


@admin.register(FeriadoPontoFacultativo)
class FeriadoPontoFacultativoAdmin(admin.ModelAdmin):
    exclude = ('id',)
    list_display = ('nome', 'data')
    ordering = ('ano', 'mes', 'dia')
    list_filter = ('ano', 'mes')

    def data(self, obj):
        return obj.data()


@admin.register(Plantonista)
class PlantonistaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone','online')
    ordering = ('nome',)
    exclude = ('criado_por', 'id')
    search_fields = ('nome',)

    def online(self, obj):
        return obj.online()
    online.short_description = 'Disponível'
    online.boolean = True

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


class OrdemPlantonistaInline(admin.TabularInline):
    model = OrdemPlantonista
    extra = 0
    fields = ('plantonista', 'ordem_na_lista')
    can_delete = False


class PlantaoInline(admin.TabularInline):
    model = Plantao
    extra = 0
    fields = ('data', 'turno', 'plantonista')
    can_delete = False

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     escala_id = request.resolver_match.kwargs.get('object_id')
    #     if escala_id:
    #         plantonistas_qs = Escala.objects.get(id=escala_id).plantonistas.all().order_by('ordem_na_lista')
    #         if db_field.name == 'plantonista':
    #             kwargs['queryset'] = plantonistas_qs
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        today = timezone.now().date()
        return qs.filter(data__gte=today)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/escala-plantao.css',)}

    fieldsets = [
        ('Informações', {'fields': ('nome', 'dois_turnos_fds', 'ativo')}),
    ]
    change_form_template = 'admin/escala_de_plantao/escala_change_form.html'
    list_display = ('nome', 'count_plantonistas', 'ativo')
    exclude = ['criado_por', 'id']
    inlines = [OrdemPlantonistaInline, PlantaoInline]
    ordering = ('nome',)

    def count_plantonistas(self, obj):
        return obj.plantonistas.count()
    count_plantonistas.short_description = 'Plantonistas'

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return super().get_queryset(request).filter(criado_por=request.user)

    def save_model(self, request, obj, form, change):
        created = not change
        if created:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
