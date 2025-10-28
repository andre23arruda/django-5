from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from cup.models import Jogo
import json


@require_POST
def save_jogo_obs(request, jogo_id):
    '''View para salvar observações do jogo via AJAX'''
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        jogo = Jogo.objects.get(pk=jogo_id)

        # Verificar permissões do usuário
        if not request.user.is_superuser and jogo.torneio.criado_por != request.user:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

        data = json.loads(request.body)
        obs = data.get('obs', '').strip()
        jogo.obs = obs
        jogo.save(update_fields=['obs'])

        return JsonResponse({
            'success': True,
            'obs': obs
        })

    except Jogo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Jogo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)