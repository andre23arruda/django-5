from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Count
from cup.models import Ranking, Torneio, Dupla, Jogo, Jogador


def get_ranking_data(request, ranking_id):
    '''Retorna informações detalhadas do ranking de torneios'''
    ranking = get_object_or_404(Ranking, slug=ranking_id, ativo=True)
    torneios = Torneio.objects.filter(ranking=ranking, ativo=False)
    num_torneios = torneios.count()

    # Contar todos os jogos de todos os torneios do ranking
    total_jogos_ranking = 0
    for torneio in torneios:
        jogos_torneio = Jogo.objects.filter(torneio=torneio, concluido='C').count()
        total_jogos_ranking += jogos_torneio

    # Buscar todas as duplas que participaram de torneios neste ranking
    duplas_ids = set()
    for torneio in torneios:
        duplas_ids.update(torneio.duplas.values_list('id', flat=True))

    duplas = Dupla.objects.filter(id__in=duplas_ids, ativo=True)
    num_duplas = len(duplas)

    # Buscar todos os jogadores únicos que participaram
    jogadores_ids = set()
    for dupla in duplas:
        if dupla.jogador1:
            jogadores_ids.add(dupla.jogador1.id)
        if dupla.jogador2:
            jogadores_ids.add(dupla.jogador2.id)

    jogadores = Jogador.objects.filter(id__in=jogadores_ids, ativo=True)
    num_jogadores = len(jogadores)

    # ===============================
    # RANKING DE DUPLAS
    # ===============================
    # duplas_stats = []

    # for dupla in duplas:
    #     # Buscar todos os jogos da dupla nos torneios deste ranking
    #     jogos = Jogo.objects.filter(
    #         Q(dupla1=dupla) | Q(dupla2=dupla),
    #         torneio__ranking=ranking,
    #         torneio__ativo=False,
    #         concluido='C'  # Apenas jogos concluídos
    #     )

    #     vitorias = 0
    #     derrotas = 0
    #     empates = 0
    #     pontos_totais = 0
    #     pontos_contra_totais = 0

    #     for jogo in jogos:
    #         # Verificar se a dupla está como dupla1 ou dupla2
    #         is_dupla1 = (jogo.dupla1 == dupla)

    #         if is_dupla1:
    #             pontos_dupla = jogo.pontos_dupla1 or 0
    #             pontos_oponente = jogo.pontos_dupla2 or 0
    #             if jogo.pontos_dupla1 > jogo.pontos_dupla2:
    #                 vitorias += 1
    #             elif jogo.pontos_dupla1 < jogo.pontos_dupla2:
    #                 derrotas += 1
    #             else:
    #                 empates += 1
    #         else:
    #             pontos_dupla = jogo.pontos_dupla2 or 0
    #             pontos_oponente = jogo.pontos_dupla1 or 0
    #             if jogo.pontos_dupla2 > jogo.pontos_dupla1:
    #                 vitorias += 1
    #             elif jogo.pontos_dupla2 < jogo.pontos_dupla1:
    #                 derrotas += 1
    #             else:
    #                 empates += 1

    #         pontos_totais += pontos_dupla
    #         pontos_contra_totais += pontos_oponente

    #     jogos_total = vitorias + derrotas + empates
    #     saldo_pontos = pontos_totais - pontos_contra_totais

    #     # Calcular percentual de vitórias
    #     percentual_vitorias = (vitorias / jogos_total * 100) if jogos_total > 0 else 0

    #     # Calcular média de pontos por jogo
    #     media_pontos = (pontos_totais / jogos_total) if jogos_total > 0 else 0

    #     duplas_stats.append({
    #         'id': dupla.id,
    #         'nome': str(dupla),
    #         'jogador1': dupla.jogador1.nome if dupla.jogador1 else None,
    #         'jogador2': dupla.jogador2.nome if dupla.jogador2 else None,
    #         'tipo': 'dupla' if dupla.jogador2 else 'simples',
    #         'vitorias': vitorias,
    #         'derrotas': derrotas,
    #         'empates': empates,
    #         'jogos_total': jogos_total,
    #         'pontos_totais': pontos_totais,
    #         'pontos_contra': pontos_contra_totais,
    #         'saldo_pontos': saldo_pontos,
    #         'media_pontos': round(media_pontos, 2),
    #         'percentual_vitorias': round(percentual_vitorias, 2)
    #     })

    # # Ordenar duplas por vitórias (desc), depois por saldo de pontos (desc), depois por média de pontos (desc)
    # duplas_stats.sort(key=lambda x: (-x['vitorias'], -x['saldo_pontos'], -x['media_pontos'], x['nome']))

    # # Adicionar posição no ranking de duplas
    # for i, dupla_stat in enumerate(duplas_stats, 1):
    #     dupla_stat['posicao'] = i

    # ===============================
    # RANKING INDIVIDUAL DE JOGADORES
    # ===============================
    jogadores_stats = []

    for jogador in jogadores:
        # Buscar todas as duplas em que o jogador participou neste ranking
        duplas_do_jogador = duplas.filter(
            Q(jogador1=jogador) | Q(jogador2=jogador)
        )

        vitorias_total = 0
        derrotas_total = 0
        empates_total = 0
        pontos_total = 0
        pontos_contra_total = 0
        jogos_total = 0
        torneios_participados = set()
        duplas_formadas = []

        for dupla in duplas_do_jogador:
            # Buscar jogos desta dupla nos torneios do ranking
            jogos_dupla = Jogo.objects.filter(
                Q(dupla1=dupla) | Q(dupla2=dupla),
                torneio__ranking=ranking,
                torneio__ativo=False,
                concluido='C'
            )

            for jogo in jogos_dupla:
                torneios_participados.add(jogo.torneio.id)

                # Verificar se a dupla está como dupla1 ou dupla2
                is_dupla1 = (jogo.dupla1 == dupla)

                if is_dupla1:
                    pontos_dupla = jogo.pontos_dupla1 or 0
                    pontos_oponente = jogo.pontos_dupla2 or 0
                    if jogo.pontos_dupla1 > jogo.pontos_dupla2:
                        vitorias_total += 1
                    elif jogo.pontos_dupla1 < jogo.pontos_dupla2:
                        derrotas_total += 1
                    else:
                        empates_total += 1
                else:
                    pontos_dupla = jogo.pontos_dupla2 or 0
                    pontos_oponente = jogo.pontos_dupla1 or 0
                    if jogo.pontos_dupla2 > jogo.pontos_dupla1:
                        vitorias_total += 1
                    elif jogo.pontos_dupla2 < jogo.pontos_dupla1:
                        derrotas_total += 1
                    else:
                        empates_total += 1

                pontos_total += pontos_dupla
                pontos_contra_total += pontos_oponente
                jogos_total += 1

            # Guardar informações sobre as duplas formadas
            parceiro = None
            if dupla.jogador1 == jogador:
                parceiro = dupla.jogador2.nome if dupla.jogador2 else "Solo"
            else:
                parceiro = dupla.jogador1.nome if dupla.jogador1 else "Solo"

            if parceiro not in [d['parceiro'] for d in duplas_formadas]:
                jogos_com_parceiro = jogos_dupla.count()
                if jogos_com_parceiro > 0:
                    duplas_formadas.append({
                        'parceiro': parceiro,
                        'jogos': jogos_com_parceiro
                    })

        saldo_pontos_total = pontos_total - pontos_contra_total

        # Calcular estatísticas
        percentual_vitorias = (vitorias_total / jogos_total * 100) if jogos_total > 0 else 0
        media_pontos = (pontos_total / jogos_total) if jogos_total > 0 else 0

        jogadores_stats.append({
            'id': jogador.id,
            'nome': jogador.nome,
            'telefone': jogador.telefone,
            'vitorias': vitorias_total,
            'derrotas': derrotas_total,
            'empates': empates_total,
            'jogos_total': jogos_total,
            'pontos_totais': pontos_total,
            'pontos_contra': pontos_contra_total,
            'saldo_pontos': saldo_pontos_total,
            'media_pontos': round(media_pontos, 2),
            'percentual_vitorias': round(percentual_vitorias, 2),
            'torneios_participados': len(torneios_participados),
            'duplas_formadas': duplas_formadas
        })

    # Ordenar jogadores por vitórias (desc), depois por saldo de pontos (desc), depois por média de pontos (desc)
    jogadores_stats.sort(key=lambda x: (-x['vitorias'], -x['saldo_pontos'], -x['media_pontos'], x['nome']))

    # Adicionar posição no ranking individual
    for i, jogador_stat in enumerate(jogadores_stats, 1):
        jogador_stat['posicao'] = i

    # Preparar resposta
    response_data = {
        'ranking': {
            'id': ranking.id,
            'nome': ranking.nome,
            'criado_em': ranking.criado_em.isoformat(),
            'criado_por': ranking.criado_por.username if ranking.criado_por else None,
        },
        'estatisticas': {
            'num_torneios': num_torneios,
            'num_duplas': num_duplas,
            'num_jogadores': num_jogadores,
            'total_jogos': total_jogos_ranking,
            'torneios': [
                {
                    'id': t.id,
                    'nome': t.nome,
                    'data': t.data.isoformat(),
                    'tipo': t.get_tipo_display(),
                    'quantidade_grupos': t.quantidade_grupos,
                    'finalizado': t.is_finished(),
                    'total_jogos': Jogo.objects.filter(torneio=t, concluido='C').count(),
                    'total_duplas': t.duplas.count()
                } for t in torneios
            ]
        },
        # 'duplas': duplas_stats,
        'jogadores': jogadores_stats  # Novo ranking individual
    }

    return JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})