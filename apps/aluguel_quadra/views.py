from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from .forms import AgendamentoForm
from .models import Aluguel


def reservar(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            try:
                aluguel = form.save()
                return redirect('aluguel_quadra:confirmacao', aluguel_id=aluguel.id)
            except Exception as e:
                messages.error(request, f'Erro ao agendar: {str(e)}')
    else:
        form = AgendamentoForm()
    return render(request, 'aluguel_quadra/reservar.html', {'form': form})


def confirmacao(request, aluguel_id: str):
    aluguel = get_object_or_404(Aluguel, id=aluguel_id)
    context = {'aluguel': aluguel}
    return render(request, 'aluguel_quadra/confirmacao.html', context)