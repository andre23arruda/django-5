from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Torneio


def create_games(request, torneio_id):
        torneio = get_object_or_404(Torneio, pk=torneio_id)
        if torneio.jogo_set.exists():
            messages.add_message(request, messages.INFO, 'Jogos já gerados para este torneio.')
        else:
            torneio.create_games()
            messages.add_message(request, messages.INFO, 'Jogos gerados com sucesso!')
        return redirect('admin:bt_league_torneio_change', torneio_id)


def see_tournament(request, torneio_id):
    torneio = get_object_or_404(Torneio, pk=torneio_id)

    # Obter jogos do torneio
    jogos = torneio.jogo_set.all()

    # Calcular ranking
    ranking = []
    for jogador in torneio.jogadores.all():
        ranking.append({
            'jogador': jogador,
            'posicao': jogador.ranking(torneio),
            'pontos': jogador.player_points(torneio),
            'vitorias': jogador.player_victories(torneio),
        })

    # Ordenar ranking por posição
    ranking = sorted(ranking, key=lambda x: x['posicao'])

    context = {
        'torneio': torneio,
        'jogos': jogos,
        'ranking': ranking
    }
    return render(request, 'see_tournament.html', context)