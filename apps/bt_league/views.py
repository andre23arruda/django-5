import base64, csv, io, os, qrcode, urllib
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Ranking, Torneio


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
    response = redirect('admin:bt_league_torneio_change', torneio_id)
    response['location'] += '#jogos-tab'
    return response


def see_tournament(request, torneio_id: str):
    '''Visualiza torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    jogos = torneio.jogo_set.all()

    # Calcular ranking
    ranking = []
    for jogador in torneio.jogadores.all():
        vitorias, pontos, saldo, n_jogos = jogador.player_points(torneio)
        ranking.append({
            'jogador': jogador,
            'pontos': pontos,
            'saldo': saldo,
            'vitorias': vitorias,
            'jogos': n_jogos
        })

    # Ordenar ranking por posição
    ranking = sorted(ranking, key=lambda x: (-x['vitorias'], -x['saldo'], -x['pontos']))
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
        'n_jogos': jogos.count(),
        'jogos_restantes': jogos.filter(concluido=False).count(),
        'ranking': ranking_result,
        'can_edit': request.user.is_superuser or torneio.criado_por == request.user,
    }
    return render(request, 'bt_league/see_league.html', context)


@login_required(redirect_field_name='next', login_url='/admin/login/')
def qrcode_tournament(request, torneio_id: str):
    '''Cria QR Code do torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    site_url = os.getenv('HOST_ADDRESS')
    img = qrcode.make(f'{ site_url }/rei-rainha/{ torneio_id }')
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
    writer.writerow(['Posição', 'Jogador', 'Vitórias', 'Saldo', 'Pontos', 'Jogos'])

    ranking = []
    for jogador in torneio.jogadores.all():
        vitorias, pontos, saldo, jogos = jogador.player_points(torneio)
        ranking.append({
            'jogador': jogador,
            'vitorias': vitorias,
            'pontos': pontos,
            'saldo': saldo,
            'jogos': jogos
        })

    # Ordenar ranking por posição
    # ranking = sorted(ranking, key=lambda x: (-x['vitorias'], -x['pontos'], -x['saldo']))
    ranking = sorted(ranking, key=lambda x: (-x['vitorias'], -x['saldo'], -x['pontos']))
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
            jogador['saldo'],
            jogador['pontos'],
            jogador['jogos']
        ])
    return response


def see_ranking(request, ranking_id: str):
    '''Visualiza o ranking geral dos jogadores em torneios'''
    ranking = get_object_or_404(Ranking, pk=ranking_id)
    torneios = Torneio.objects.filter(ranking=ranking)
    jogadores = {}
    for torneio in torneios:
        for jogador in torneio.jogadores.all():
            vitorias, pontos, saldo, jogos = jogador.player_points(torneio)
            if jogador.id not in jogadores:
                jogadores[jogador.id] = {
                    'jogador': jogador.nome,
                    'vitorias': vitorias,
                    'saldo': saldo,
                    'pontos': pontos,
                    'jogos': jogos
                }
            else:
                jogadores[jogador.id]['vitorias'] += vitorias
                jogadores[jogador.id]['saldo'] += saldo
                jogadores[jogador.id]['pontos'] += pontos
                jogadores[jogador.id]['jogos'] += jogos

    jogadores = list(jogadores.values())
    jogadores = sorted(jogadores, key=lambda x: (-x['vitorias'], -x['saldo'], -x['pontos'], x['jogos']))
    jogadores_ranking = []
    j_0 = {'pontos': 0, 'saldo': 0, 'vitorias': 0, 'posicao': 1}
    for i, j_1 in enumerate(jogadores):
        if (j_1['pontos'] == j_0['pontos']) and (j_1['saldo'] == j_0['saldo']) and (j_1['vitorias'] == j_0['vitorias']):
            j_1['posicao'] = j_0['posicao']
        else:
            j_1['posicao'] = i + 1
            j_0 = j_1
        jogadores_ranking.append(j_1)

    context = {
        'ranking': ranking,
        'jogadores': jogadores_ranking
    }
    return render(request, 'bt_league/see_ranking.html', context)