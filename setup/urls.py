from django.contrib import admin
from django.urls import include, path
from .views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('torneio/', include('bt_cup.urls')),
    path('torneio-v2/', include('cup.urls')),
    path('rei-rainha/', include('bt_league.urls')),
    path('quadras/', include('aluguel_quadra.urls')),
    path('escala-plantao/', include('escala_de_plantao.urls')),
]

admin.site.index_title = 'Dashboard'
admin.site.site_header = 'Dashboard'
admin.site.site_title  = 'Dashboard'