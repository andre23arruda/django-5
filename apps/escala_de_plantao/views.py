from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Escala


@login_required(redirect_field_name='next', login_url='/admin/login/')
def create_plantoes(request, escala_id: int):
    '''Cria plantões de uma escala'''
    escala = get_object_or_404(Escala, pk=escala_id)
    result = escala.create_plantoes()
    if result:
        messages.add_message(request, messages.INFO, 'Escala gerada com sucesso!')
    else:
        messages.add_message(request, messages.ERROR, 'Plantões já criados para o mês atual!')
    return redirect('admin:escala_de_plantao_escala_change', escala_id)


def see_escala(request, escala_id: int):
    '''Visualiza escala de plantões'''
    escala = get_object_or_404(Escala, pk=escala_id)
    plantoes = escala.plantao_set.all()
    context = {
        'escala': escala,
        'plantoes': plantoes,
        'mes_atual': timezone.now().date().strftime('%m/%Y'),
    }
    return render(request, 'escala_de_plantao/see_escala.html', context)


def see_all_escalas(request, escala_id: int):
    '''Visualiza escala de plantões'''
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