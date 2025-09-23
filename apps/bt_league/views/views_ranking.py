from django.shortcuts import render, get_object_or_404

from bt_league.models import Ranking, Torneio


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
