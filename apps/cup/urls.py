from django.urls import path
from .views import (
    create_games,
    export_csv,
    finish_tournament,
    next_stage,
    qrcode_tournament,
    see_tournament,
    get_ranking_data,
    get_tournament_data,
    save_jogo_obs,
    save_game
)

app_name = 'cup'

urlpatterns = [
    path('<str:torneio_id>/', see_tournament, name='see_tournament'),
    path('<str:torneio_id>/criar-jogos', create_games, name='create_games'),
    path('<str:torneio_id>/download', export_csv, name='download'),
    path('<str:torneio_id>/encerrar', finish_tournament, name='finish_tournament'),
    path('<str:torneio_id>/proxima-fase', next_stage, name='next_stage'),
    path('<str:torneio_id>/qr-code', qrcode_tournament, name='qrcode_tournament'),
    path('<str:torneio_id>/json', get_tournament_data, name='tournament_data'),
    path('ranking/<str:ranking_id>/json', get_ranking_data, name='ranking_data'),
    path('<str:jogo_id>/save-obs/', save_jogo_obs, name='save_jogo_obs'),
    path('<str:jogo_id>/save-game/', save_game, name='save_game'),
]