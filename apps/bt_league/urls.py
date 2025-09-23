from django.urls import path
from .views import (
    create_games,
    export_csv,
    finish_tournament,
    qrcode_tournament,
    see_tournament,
    see_ranking,
    get_ranking_data,
    get_tournament_data
)

app_name = 'bt_league'

urlpatterns = [
    path('<str:torneio_id>/', see_tournament, name='see_tournament'),
    path('<str:torneio_id>/criar-jogos', create_games, name='create_games'),
    path('<str:torneio_id>/download', export_csv, name='download'),
    path('<str:torneio_id>/encerrar', finish_tournament, name='finish_tournament'),
    path('<str:torneio_id>/qr-code', qrcode_tournament, name='qrcode_tournament'),
    path('<str:torneio_id>/json', get_tournament_data, name='tournament_data'),
    path('ranking/<str:ranking_id>/', see_ranking, name='see_ranking'),
    path('ranking/<str:ranking_id>/json', get_ranking_data, name='ranking_data'),
]