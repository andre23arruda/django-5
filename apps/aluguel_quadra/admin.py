from django.contrib import admin
from .models import Aluguel, Quadra


@admin.register(Aluguel)
class AluguelAdmin(admin.ModelAdmin):
    exclude = ('id',)
    list_display = ('quadra', 'data', 'inicio', 'fim', 'cliente_nome', 'cliente_telefone', 'valor_total', 'pago')
    ordering = ('-data', '-inicio')


@admin.register(Quadra)
class QuadraAdmin(admin.ModelAdmin):
    exclude = ('id',)
    list_display = ('nome', 'tipo', 'preco_hora', 'disponivel')
    ordering = ('nome', 'disponivel')
