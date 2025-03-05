import locale
from collections import defaultdict
from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Escala

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')


def calendario_plantoes(request, escala_id: str):
    escala = get_object_or_404(Escala, pk=escala_id)
    calendarios = gerar_calendario_plantoes(escala)

    context = {
        'calendarios': calendarios,
        'escala': escala,
    }
    return render(request, 'escala_de_plantao/see_calendario_escala.html', context)


@login_required(redirect_field_name='next', login_url='/admin/login/')
def create_plantoes(request, escala_id: str):
    '''Cria plantões de uma escala'''
    user = request.user
    escala = get_object_or_404(Escala, pk=escala_id)
    result = escala.create_plantoes(user)
    if result:
        messages.add_message(request, messages.INFO, 'Escala gerada com sucesso!')
    else:
        messages.add_message(request, messages.ERROR, 'Plantões já criados para o mês atual!')
    return redirect('admin:escala_de_plantao_escala_change', escala_id)


def see_escala(request, escala_id: str):
    '''Visualiza escala de plantões'''
    escala = get_object_or_404(Escala, pk=escala_id)
    plantoes = escala.plantao_set.all()
    context = {
        'escala': escala,
        'plantoes': plantoes,
        'mes_atual': timezone.now().date().strftime('%m/%Y'),
    }
    return render(request, 'escala_de_plantao/see_escala.html', context)


def see_all_escalas(request, escala_id: str):
    '''Visualiza escala de plantões em tabela'''
    escala = get_object_or_404(Escala, pk=escala_id)
    plantoes = escala.plantao_set.all()
    plantoes_por_meses = {}

    for plantao in plantoes.annotate(mes_ano=TruncMonth('data')).order_by('-mes_ano'):
        key = plantao.mes_ano.strftime('%m/%Y')
        if key not in plantoes_por_meses:
            plantoes_por_meses[key] = []
        plantoes_por_meses[key].append(plantao)

    context = {
        'escala': escala,
        'plantoes_por_meses': plantoes_por_meses,
    }
    return render(request, 'escala_de_plantao/see_all_escalas.html', context)


def gerar_calendario_plantoes(escala):
    calendarios_por_mes = {}
    plantoes = escala.plantao_set.all()
    plantoes_por_meses = {}

    for plantao in plantoes.annotate(mes_ano=TruncMonth('data')).order_by('-mes_ano'):
        key = plantao.mes_ano.strftime('%m/%Y')
        if key not in plantoes_por_meses:
            plantoes_por_meses[key] = []
        plantoes_por_meses[key].append(plantao)

    for mes_ano, plantoes_mes in plantoes_por_meses.items():
        mes, ano = mes_ano.split('/')
        calendario = []
        primeiro_dia = date(int(ano), int(mes), 1)

        # Cria dicionário de plantões por data para este mês
        plantoes_do_mes = defaultdict(list)
        for plantao in plantoes_mes:
            plantoes_do_mes[plantao.data].append(plantao)

        # Gera calendário
        calendario = []
        dia_atual = primeiro_dia

        # Adiciona dias vazios antes do primeiro dia do mês
        while dia_atual.weekday() != 0:  # Até chegar na segunda-feira
            dia_atual -= timedelta(days=1)

        # Gera 6 semanas de calendário
        while len(calendario) < 6 * 7:
            dia_info = {
                'data': dia_atual,
                'dia': dia_atual.day,
                'dia_semana': dia_atual.strftime('%A'),
                'plantoes': plantoes_do_mes.get(dia_atual, []),
                'is_current_month': dia_atual.month == int(mes)
            }
            calendario.append(dia_info)
            dia_atual += timedelta(days=1)

        # Armazena o calendário do mês
        calendarios_por_mes[mes_ano] = [calendario[i:i+7] for i in range(0, len(calendario), 7)]

    return calendarios_por_mes
