from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from bt_league.models import Ranking, Torneio, Jogador, Jogo


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


def get_ranking_data(request, ranking_id):
    '''informações detalhadas de um Ranking'''
    ranking = get_object_or_404(Ranking, slug=ranking_id, ativo=True)
    torneios = Torneio.objects.filter(ranking=ranking, ativo=False)
    num_torneios = torneios.count()

    total_jogos_ranking = 0
    for torneio in torneios:
        jogos_torneio = Jogo.objects.filter(torneio=torneio, concluido='C').count()
        total_jogos_ranking += jogos_torneio

    # Buscar todos os jogadores que participaram de torneios neste ranking
    jogadores_ids = set()
    for torneio in torneios:
        jogadores_ids.update(torneio.jogadores.values_list('id', flat=True))
    jogadores = Jogador.objects.filter(id__in=jogadores_ids)
    num_jogadores = len(jogadores)

    # Calcular estatísticas de cada jogador no ranking
    jogadores_stats = []
    for jogador in jogadores:
        # Buscar todos os jogos do jogador nos torneios deste ranking
        jogos = Jogo.objects.filter(
            Q(dupla1_jogador1=jogador) | Q(dupla1_jogador2=jogador) |
            Q(dupla2_jogador1=jogador) | Q(dupla2_jogador2=jogador),
            torneio__ranking=ranking,
            concluido='C'
        )

        vitorias = 0
        derrotas = 0
        pontos_totais = 0
        pontos_contra_totais = 0

        for jogo in jogos:
            # Verificar se o jogador está na dupla 1 ou dupla 2
            is_dupla1 = (jogo.dupla1_jogador1 == jogador or jogo.dupla1_jogador2 == jogador)

            if is_dupla1:
                pontos_jogador = jogo.placar_dupla1 or 0
                pontos_oponente = jogo.placar_dupla2 or 0
                if jogo.placar_dupla1 > jogo.placar_dupla2:
                    vitorias += 1
                else:
                    derrotas += 1
            else:
                pontos_jogador = jogo.placar_dupla2 or 0
                pontos_oponente = jogo.placar_dupla1 or 0
                if jogo.placar_dupla2 > jogo.placar_dupla1:
                    vitorias += 1
                else:
                    derrotas += 1

            pontos_totais += pontos_jogador
            pontos_contra_totais += pontos_oponente

        jogos_total = vitorias + derrotas
        saldo_pontos = pontos_totais - pontos_contra_totais

        # Calcular percentual de vitórias
        percentual_vitorias = (vitorias / jogos_total * 100) if jogos_total > 0 else 0

        jogadores_stats.append({
            'id': jogador.id,
            'nome': jogador.nome,
            'nome_curto': jogador.short_name(),
            'vitorias': vitorias,
            'derrotas': derrotas,
            'jogos_total': jogos_total,
            'pontos_totais': pontos_totais,
            'pontos_contra': pontos_contra_totais,
            'saldo_pontos': saldo_pontos,
            'percentual_vitorias': round(percentual_vitorias, 2)
        })

    # Ordenar jogadores por vitórias (desc), depois por saldo de pontos (desc)
    jogadores_stats.sort(key=lambda x: (-x['vitorias'], -x['saldo_pontos'], x['jogos_total']))

    # Adicionar posição no ranking
    for i, jogador_stat in enumerate(jogadores_stats, 1):
        jogador_stat['posicao'] = i

    # Preparar resposta
    result = {
        'ranking': {
            'id': ranking.id,
            'nome': ranking.nome,
            'jogos': total_jogos_ranking
        },
        'estatisticas': {
            'num_torneios': num_torneios,
            'num_jogadores': num_jogadores,
            'torneios': [
                {
                    'id': t.id,
                    'nome': t.nome,
                    'jogos': t.jogo_set.all().count(),
                    'jogadores': t.jogadores.count(),
                    'data': t.data.isoformat(),
                    'finalizado': t.is_finished()
                } for t in torneios
            ]
        },
        'jogadores': jogadores_stats
    }

    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})