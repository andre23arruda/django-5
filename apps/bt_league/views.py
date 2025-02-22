import base64, io, os, qrcode, urllib
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Torneio

@login_required(redirect_field_name='next', login_url='/admin/login/')
def create_games(request, torneio_id: str):
    '''Cria jogos para o torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    result = torneio.create_games()
    if isinstance(result, Exception):
        messages.add_message(request, messages.ERROR, result)
    else:
        messages.add_message(request, messages.INFO, 'Jogos gerados com sucesso!')
    response = redirect('admin:bt_league_torneio_change', torneio_id)
    response['location'] += '#jogos-tab'
    return response


def finish_tournament(request, torneio_id: str):
    '''Finaliza torneio e desabilita todas os jogadores'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    torneio.finish()
    messages.add_message(request, messages.SUCCESS, f'{ torneio } finalizado!')
    return redirect('admin:bt_league_torneio_changelist')


def see_tournament(request, torneio_id: str):
    '''Visualiza torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)

    # Obter jogos do torneio
    jogos = torneio.jogo_set.all()

    # Calcular ranking
    ranking = []
    for jogador in torneio.jogadores.all():
        vitorias, pontos = jogador.player_points(torneio)
        ranking.append({
            'jogador': jogador,
            'posicao': jogador.ranking(torneio),
            'pontos': pontos,
            'vitorias': vitorias
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
def qrcode_tournament(request, torneio_id: str):
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
    return render(request, 'qrcode_tournament.html', context)
