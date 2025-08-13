from django.contrib import admin
from django.urls import include, path
from .views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('torneio/', include('bt_cup.urls')),
    path('rei-rainha/', include('bt_league.urls')),
    path('quadras/', include('aluguel_quadra.urls')),
    path('escala-plantao/', include('escala_de_plantao.urls')),
]

admin.site.index_title = 'Painel de Gestão'
admin.site.site_header = 'Painel de Gestão'
admin.site.site_title  = 'Painel de Gestão'