from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from .views import (
    index, check_auth, check_otp,
    get_csrf_token, staff_login,
)

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('api/torneio-v1/', include('bt_cup.urls')),
    path('api/torneio/', include('cup.urls')),
    path('api/rei-rainha/', include('bt_league.urls')),
    path('check-auth', check_auth, name='check_auth'),
    path('check-otp', check_otp, name='check_otp'),
    path('csrf', get_csrf_token, name='get_csrf_token'),
    path('staff-login', staff_login, name='staff_login'),
    path('quadras/', include('aluguel_quadra.urls')),
    path('escala-plantao/', include('escala_de_plantao.urls')),
]
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.index_title = 'Dashboard'
admin.site.site_header = 'Dashboard'
admin.site.site_title  = 'Dashboard'