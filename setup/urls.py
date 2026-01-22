from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from .views import index, check_auth, get_csrf_token, staff_login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('check-auth', check_auth, name='check_auth'),
    path('csrf', get_csrf_token, name='get_csrf_token'),
    path('staff_login', staff_login, name='staff_login'),
    path('torneio-v1/', include('bt_cup.urls')),
    path('torneio/', include('cup.urls')),
    path('rei-rainha/', include('bt_league.urls')),
    path('quadras/', include('aluguel_quadra.urls')),
    path('escala-plantao/', include('escala_de_plantao.urls')),
]

admin.site.index_title = 'Dashboard'
admin.site.site_header = 'Dashboard'
admin.site.site_title  = 'Dashboard'