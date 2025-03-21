import base64, csv, io, os, qrcode, urllib
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
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
        messages.add_message(request, messages.INFO, f'{ len(result )} jogos gerados com sucesso!')
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
        vitorias, pontos, saldo = jogador.player_points(torneio)
        ranking.append({
            'jogador': jogador,
            'pontos': pontos,
            'saldo': saldo,
            'vitorias': vitorias
        })

    # Ordenar ranking por posição
    ranking = sorted(ranking, key=lambda x: (-x['vitorias'], -x['pontos'], -x['saldo']))
    ranking_result = []
    j_0 = {'pontos': 0, 'saldo': 0, 'vitorias': 0, 'posicao': 1}
    for i, j_1 in enumerate(ranking):
        if (j_1['pontos'] == j_0['pontos']) and (j_1['saldo'] == j_0['saldo']) and (j_1['vitorias'] == j_0['vitorias']):
            j_1['posicao'] = j_0['posicao']
        else:
            j_1['posicao'] = i + 1
            j_0 = j_1
        ranking_result.append(j_1)

    context = {
        'torneio': torneio,
        'jogos': jogos,
        'ranking': ranking_result
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


def export_csv(request, torneio_id: str):
    '''Gera um arquivo CSV com os dados dos jogadores'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{ torneio.nome }.csv"'
    writer = csv.writer(response)
    writer.writerow(['Posição', 'Jogador', 'Vitórias', 'Pontos', 'Saldo'])

    ranking = []
    for jogador in torneio.jogadores.all():
        vitorias, pontos, saldo = jogador.player_points(torneio)
        ranking.append({
            'jogador': jogador,
            'vitorias': vitorias,
            'pontos': pontos,
            'saldo': saldo,
        })

    # Ordenar ranking por posição
    ranking = sorted(ranking, key=lambda x: (-x['vitorias'], -x['pontos'], -x['saldo']))
    ranking_result = []
    j_0 = {'pontos': 0, 'saldo': 0, 'vitorias': 0, 'posicao': 1}
    for i, j_1 in enumerate(ranking):
        if (j_1['pontos'] == j_0['pontos']) and (j_1['saldo'] == j_0['saldo']) and (j_1['vitorias'] == j_0['vitorias']):
            j_1['posicao'] = j_0['posicao']
        else:
            j_1['posicao'] = i + 1
            j_0 = j_1
        ranking_result.append(j_1)

    for jogador in ranking_result:
        writer.writerow([
            jogador['posicao'],
            jogador['jogador'].nome,
            jogador['vitorias'],
            jogador['pontos'],
            jogador['saldo']
        ])
    return response
