import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from bt_league.models import Jogo


@require_POST
@login_required(redirect_field_name='next', login_url='/admin/login/')
def save_game(request, jogo_id):
    '''View para salvar automaticamente status e placar do jogo'''
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized'
        }, status=403)

    try:
        jogo = Jogo.objects.get(pk=jogo_id)

        # Verificar permissões do usuário
        if not request.user.is_superuser and jogo.torneio.criado_por != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Sem permissão'
            }, status=403)

        data = json.loads(request.body)
        status = data.get('status')
        placar_dupla1 = data.get('placar_dupla1')
        placar_dupla2 = data.get('placar_dupla2')

        # Validar status
        if status not in ['P', 'A', 'C']:
            return JsonResponse({
                'success': False,
                'error': 'Status inválido'
            }, status=400)

        # Atualizar o jogo
        jogo.concluido = status

        # Atualizar pontos se fornecidos
        if placar_dupla1 is not None:
            try:
                jogo.placar_dupla1 = int(placar_dupla1) if placar_dupla1 != '' else None
            except (ValueError, TypeError):
                jogo.placar_dupla1 = None

        if placar_dupla2 is not None:
            try:
                jogo.placar_dupla2 = int(placar_dupla2) if placar_dupla2 != '' else None
            except (ValueError, TypeError):
                jogo.placar_dupla2 = None

        jogo.save()

        return JsonResponse({
            'success': True,
            'jogo_id': jogo_id,
            'status': jogo.concluido,
            'placar_dupla1': jogo.placar_dupla1,
            'placar_dupla2': jogo.placar_dupla2
        })

    except Jogo.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Jogo não encontrado'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)