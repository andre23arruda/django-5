import base64, io, os, qrcode, urllib
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Torneio

@login_required(redirect_field_name='next', login_url='/admin/login/')
def create_games(request, torneio_id: int):
    '''Cria jogos para o torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    if torneio.jogo_set.exists():
        messages.add_message(request, messages.INFO, 'Jogos já gerados para este torneio.')
    else:
        torneio.create_games()
        messages.add_message(request, messages.INFO, 'Jogos gerados com sucesso!')
    return redirect('admin:bt_league_torneio_change', torneio_id)


def see_tournament(request, torneio_id: int):
    '''Visualiza torneio'''
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
    return render(request, 'bt_league/see_tournament.html', context)


@login_required(redirect_field_name='next', login_url='/admin/login/')
def qrcode_tournament(request, torneio_id: int):
    '''Cria QR Code do torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    site_url = os.getenv('HOST_ADDRESS')
    img = qrcode.make(f'{ site_url }/torneio/{ torneio_id }')
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri =  urllib.parse.quote(string)
    context = {
        'img_b64': uri,
        'torneio': torneio,
    }
    return render(request, 'bt_league/qrcode_tournament.html', context)