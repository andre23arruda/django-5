from django.urls import path
from . import views

app_name = 'bt_league'

urlpatterns = [
    path('<int:torneio_id>/', views.see_tournament, name='see_tournament'),
    path('<int:torneio_id>/criar-jogos', views.create_games, name='create_games'),
]