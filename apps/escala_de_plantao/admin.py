from django.contrib import admin
from .models import FeriadoPontoFacultativo, Escala, Plantao, Plantonista

from django.conf.locale.pt_BR import formats as portuguese
from django.conf.locale.en import formats as english

portuguese.DATE_FORMAT = 'd/m/Y'
portuguese.DATETIME_FORMAT = 'H:i d/m/Y'
english.DATE_FORMAT = 'd/m/Y'
english.DATETIME_FORMAT = 'H:i d/m/Y'


@admin.register(FeriadoPontoFacultativo)
class FeriadoPontoFacultativoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    ordering = ('ano', 'mes', 'dia')

    def data(self, obj):
        return obj.data()


@admin.register(Plantonista)
class PlantonistaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'ordem_na_lista', 'online')
    ordering = ('ordem_na_lista',)
    exclude = ('criado_por',)
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


class PlantaoInline(admin.TabularInline):
    model = Plantao
    extra = 0
    fields = ('data', 'turno', 'plantonista')
    can_delete = False

    def get_queryset(self, request):
        from django.utils import timezone
        qs = super().get_queryset(request)
        today = timezone.now().date()
        return qs.filter(data__gte=today)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('css/escala-plantao.css',)}

    change_form_template = 'admin/escala_de_plantao/escala_change_form.html'
    list_display = ('nome', 'count_plantonistas', 'ativo')
    readonly_fields = ['criado_por']
    autocomplete_fields = ('plantonistas',)
    inlines = [PlantaoInline]

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
