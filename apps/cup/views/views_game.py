import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from cup.models import Jogo


@require_POST
@login_required(redirect_field_name='next', login_url='/admin/login/')
def save_jogo_obs(request, jogo_id):
    '''View para salvar observações do jogo via AJAX'''
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
                'error': 'Unauthorized'
            }, status=403)

        data = json.loads(request.body)
        obs = data.get('obs', '').strip()
        jogo.obs = obs
        jogo.save(update_fields=['obs'])

        return JsonResponse({
            'success': True,
            'obs': obs
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
        pontos_dupla1 = data.get('pontos_dupla1')
        pontos_dupla2 = data.get('pontos_dupla2')

        # Validar status
        if status not in ['A', 'C']:
            return JsonResponse({
                'success': False,
                'error': 'Status inválido'
            }, status=400)

        # Atualizar o jogo
        jogo.concluido = status

        # Atualizar pontos se fornecidos
        if pontos_dupla1 is not None:
            try:
                jogo.pontos_dupla1 = int(pontos_dupla1) if pontos_dupla1 != '' else None
            except (ValueError, TypeError):
                jogo.pontos_dupla1 = None

        if pontos_dupla2 is not None:
            try:
                jogo.pontos_dupla2 = int(pontos_dupla2) if pontos_dupla2 != '' else None
            except (ValueError, TypeError):
                jogo.pontos_dupla2 = None

        jogo.save()

        return JsonResponse({
            'success': True,
            'jogo_id': jogo_id,
            'status': jogo.concluido,
            'pontos_dupla1': jogo.pontos_dupla1,
            'pontos_dupla2': jogo.pontos_dupla2
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