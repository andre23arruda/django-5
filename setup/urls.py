from django.contrib import admin
from django.urls import include, path
from .views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('copa/', include('bt_cup.urls')),
    path('torneio/', include('bt_league.urls')),
    path('quadras/', include('aluguel_quadra.urls')),
    path('plantao/', include('escala_de_plantao.urls')),
]

admin.site.index_title = 'Meu Admin'
admin.site.site_header = 'Meu Admin'
admin.site.site_title  = 'Meu Admin'