from django.urls import path
from .views import (
    create_games,
    finish_tournament,
    next_stage,
    qrcode_tournament,
    see_tournament,
)

app_name = 'bt_cup'

urlpatterns = [
    path('<str:torneio_id>/', see_tournament, name='see_tournament'),
    path('<str:torneio_id>/criar-jogos', create_games, name='create_games'),
    path('<str:torneio_id>/encerrar', finish_tournament, name='finish_tournament'),
    path('<str:torneio_id>/proxima-fase', next_stage, name='next_stage'),
    path('<str:torneio_id>/qr-code', qrcode_tournament, name='qrcode_tournament'),
]