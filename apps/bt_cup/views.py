import base64, io, os, qrcode, urllib
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Jogo, Torneio


def distribute_classifieds(classifieds):
    '''Distribui classificados [1,2,3,4,5,6,7,8,9,10] -> [1,10,2,9,3,8,4,7,5,6]'''
    result = []
    while classifieds:
        if classifieds:
            result.append(classifieds.pop(0))
        if classifieds:
            result.append(classifieds.pop(-1))
    return result


@login_required(redirect_field_name='next', login_url='/admin/login/')
def create_games(request, torneio_id: str):
    '''Cria jogos para o torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    if torneio.jogo_set.exists():
        messages.add_message(request, messages.ERROR, 'Jogos já gerados para este torneio.')
    else:
        result = torneio.create_games()
        if isinstance(result, Exception):
            messages.add_message(request, messages.ERROR, result)
        else:
            messages.add_message(request, messages.INFO, 'Jogos gerados com sucesso!')

    response = redirect('admin:bt_cup_torneio_change', torneio_id)
    response['location'] += '#jogos-tab'
    return response


def finish_tournament(request, torneio_id: str):
    '''Finaliza torneio e desabilita todas as duplas'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    torneio.finish()
    messages.add_message(request, messages.SUCCESS, f'{ torneio } finalizado!')
    return redirect('admin:bt_cup_torneio_changelist')


@login_required(redirect_field_name='next', login_url='/admin/login/')
def next_stage(request, torneio_id: str):
    '''Processa grupos e vai para a próxima fase'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    jogos = torneio.jogo_set.all()
    jogos_preenchidos = jogos.filter(
        fase__in=['OITAVAS', 'QUARTAS', 'SEMIFINAIS', 'FINAL'],
        dupla1__isnull=False,
        dupla2__isnull=False
    )
    jogos_grupos_nao_finalizados = jogos.filter(
        fase__startswith='GRUPO',
        concluido=False
    )

    if jogos_grupos_nao_finalizados.exists():
        messages.add_message(request, messages.ERROR, 'Jogos de grupos ainda não foram finalizados.')
    elif jogos_preenchidos:
        result = torneio.next_stage()
        if isinstance(result, Exception):
            messages.add_message(request, messages.ERROR, result)
        else:
            messages.add_message(request, messages.INFO, 'Confrontos gerados com sucesso!')
    else:
        classificados = torneio.process_groups()
        classificados = distribute_classifieds(classificados)
        for i in range(0, len(classificados), 2):
            dupla1, dupla2 = classificados[i:i+2]
            if torneio.quantidade_grupos == 1:
                final = jogos.get(fase='FINAL')
                final.dupla1 = dupla1
                final.dupla2 = dupla2
                final.save()
            elif torneio.quantidade_grupos == 2:
                semifinal = jogos.filter(fase='SEMIFINAIS')[i//2]
                semifinal.dupla1 = dupla1
                semifinal.dupla2 = dupla2
                semifinal.save()
            elif torneio.quantidade_grupos == 4:
                quartas = jogos.filter(fase='QUARTAS')[i//2]
                quartas.dupla1 = dupla1
                quartas.dupla2 = dupla2
                quartas.save()
            elif torneio.quantidade_grupos == 8:
                oitavas = jogos.filter(fase='OITAVAS')[i//2]
                oitavas.dupla1 = dupla1
                oitavas.dupla2 = dupla2
        messages.add_message(request, messages.INFO, 'Confrontos gerados com sucesso!')

    response = redirect('admin:bt_cup_torneio_change', torneio_id)
    response['location'] += '#jogos-tab'
    return response


def see_tournament(request, torneio_id: str):
    '''Visualiza torneio'''
    torneio = Torneio.objects.get(id=torneio_id)
    jogos = Jogo.objects.filter(torneio=torneio)
    classificacao = torneio.get_groups_ranking()

    # Separar jogos por grupos
    grupos = {}
    for i in range(1, 5):  # Grupos 1 a 4
        grupo_jogos = jogos.filter(fase=f'GRUPO {i}')
        if grupo_jogos.exists():
            grupos[f'GRUPO {i}'] = {
                'jogos': grupo_jogos,
                'classificacao': classificacao[f'GRUPO {i}']
            }

    # Separar jogos das próximas fases
    proximas_fases = {}
    for fase in ['OITAVAS', 'QUARTAS']:
        fase_jogos = jogos.filter(fase=fase)
        if fase_jogos.exists():
            proximas_fases[fase] = fase_jogos

    # Separar fases finais (semifinais e final)
    fases_finais = {}
    for fase in ['SEMIFINAIS', 'FINAL']:
        fase_jogos = jogos.filter(fase=fase)
        if fase_jogos.exists():
            fases_finais[fase] = fase_jogos

    context = {
        'torneio': torneio,
        'grupos': grupos,
        'proximas_fases': proximas_fases,
        'fases_finais': fases_finais,
        'classificacao': classificacao
    }

    return render(request, 'bt_cup/see_tournament.html', context)


@login_required(redirect_field_name='next', login_url='/admin/login/')
def qrcode_tournament(request, torneio_id: str):
    '''Cria QR Code do torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    site_url = os.getenv('HOST_ADDRESS')
    img = qrcode.make(f'{ site_url }/copa/{ torneio_id }')
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
