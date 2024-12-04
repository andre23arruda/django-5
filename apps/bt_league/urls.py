from django.urls import path
from .views import create_games, qrcode_tournament, see_tournament

app_name = 'bt_league'

urlpatterns = [
    path('<int:torneio_id>/', see_tournament, name='see_tournament'),
    path('<int:torneio_id>/criar-jogos', create_games, name='create_games'),
    path('<int:torneio_id>/qr-code', qrcode_tournament, name='qrcode_tournament'),
]