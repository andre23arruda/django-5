import base64, io, json, os, qrcode, urllib
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from PIL import Image as PILImage

from ..models import Jogador, Dupla, Jogo, Torneio


@login_required(redirect_field_name='next', login_url='/admin/login/')
def create_games(request, torneio_id: str):
    '''Cria jogos para o torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    result = torneio.create_games()
    if isinstance(result, Exception):
        messages.add_message(request, messages.ERROR, result)
    else:
        messages.add_message(request, messages.INFO, 'Jogos gerados com sucesso!')
    response = redirect('admin:futevolei_torneio_change', torneio_id)
    response['location'] += '#jogos-tab'
    return response


@login_required(redirect_field_name='next', login_url='/admin/login/')
def finish_tournament(request, torneio_id: str):
    '''Finaliza torneio e desabilita todas as duplas'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    torneio.finish()
    messages.add_message(request, messages.SUCCESS, f'{ torneio } finalizado!')
    response = redirect('admin:futevolei_torneio_change', torneio_id)
    response['location'] += '#jogos-tab'
    return response


@login_required(redirect_field_name='next', login_url='/admin/login/')
def next_stage(request, torneio_id: str):
    '''Processa grupos e vai para a próxima fase'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    result = torneio.next_stage()
    messages.add_message(request, messages.INFO, 'Confrontos gerados com sucesso!')
    response = redirect('admin:futevolei_torneio_change', torneio_id)
    response['location'] += '#jogos-tab'
    return response


@login_required(redirect_field_name='next', login_url='/admin/login/')
def qrcode_tournament(request, torneio_id: str):
    '''Cria QR Code do torneio'''
    torneio = get_object_or_404(Torneio, pk=torneio_id)
    link = f'{ os.getenv("APP_LINK") }/futevolei/{ torneio.slug }'

    logo_link = settings.BASE_DIR / 'setup/static/images/favicon-qr-code.png'
    logo = PILImage.open(logo_link).convert('RGBA')
    basewidth = 100
    wpercent = (basewidth / float(logo.size[0]))
    hsize = int((float(logo.size[1]) * float(wpercent)))
    logo = logo.resize((basewidth, hsize), PILImage.LANCZOS)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color='white', back_color='black').convert('RGB')
    pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
    img.paste(logo, pos, logo)

    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    context = {
        'img_b64': uri,
        'torneio': torneio,
    }
    return render(request, 'qrcode_tournament.html', context)


def get_tournament_data(request, torneio_id: str):
    '''Returns tournament data as JSON for React frontend'''
    CARD_STYLE_DICT = {
        'FASE 1': '1/2',
        'FASE 2': '1/2',
        'FASE 3': '1/2',
        'FASE 4': '1/2',
        'FASE 5': '1/4',
        'FASE 6': '1/4',
        'FASE 7': '1/6',
        'FASE 8': '1/6',
    }
    torneio = Torneio.objects.filter(slug=torneio_id).first()
    if not torneio:
        return JsonResponse({'error': 'Torneio não encontrado'}, status=404)
    jogos = Jogo.objects.filter(torneio=torneio)
    nao_iniciado = (jogos.count() == 0) or (jogos.filter(concluido='P').count() == jogos.count())

    playoff_card_style = ''

    # Process playoffs
    fases = {}
    for fase in ['FASE 1', 'FASE 2', 'FASE 3', 'FASE 4', 'FASE 5', 'FASE 6', 'FASE 7', 'FASE 8']:
        fase_jogos = jogos.filter(fase=fase)
        if fase_jogos.exists():
            fases[fase] = [
                {
                    'id': jogo.id,
                    'dupla1': jogo.dupla1.render() if jogo.dupla1 else None,
                    'dupla2': jogo.dupla2.render() if jogo.dupla2 else None,
                    'pontos_dupla1': jogo.pontos_dupla1,
                    'pontos_dupla2': jogo.pontos_dupla2,
                    'concluido': jogo.concluido,
                    'playoff_number': jogo.playoff_number,
                    'obs': jogo.obs,
                    'help_text': jogo.playoff_help_text or '',
                } for jogo in fase_jogos
            ]
            playoff_card_style = CARD_STYLE_DICT[fase]

    data = {
        'torneio': {
            'id': torneio.id,
            'nome': torneio.nome,
            'data': torneio.data,
            'tipo': torneio.tipo,
            'ativo': torneio.ativo,
            'duplas': torneio.duplas.count(),
            'jogos': jogos.count(),
            'jogos_restantes': jogos.exclude(concluido='C').count(),
            'nao_iniciado': nao_iniciado
        },
        'jogos': fases,
        'can_edit': torneio.ativo and (request.user.is_superuser or torneio.criado_por == request.user),
        'card_style': playoff_card_style,
    }

    return JsonResponse(data)
