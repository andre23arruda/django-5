from django.urls import path
from .views import create_games, next_stage, see_tournament, qrcode_tournament

app_name = 'bt_cup'

urlpatterns = [
    path('<int:torneio_id>/criar-jogos', create_games, name='create_games'),
    path('<int:torneio_id>/proxima-fase', next_stage, name='next_stage'),
    path('<int:torneio_id>/', see_tournament, name='see_tournament'),
    path('<int:torneio_id>/qr-code', qrcode_tournament, name='qrcode_tournament'),
]