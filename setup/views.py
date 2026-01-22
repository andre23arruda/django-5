import json
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods


def index(request):
    return render(request, 'index.html')


@require_http_methods(['GET'])
def check_auth(request):
    '''Verifica se o usuário está autenticado'''
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'username': request.user.username,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
        })
    return JsonResponse({
        'authenticated': False
    })


@ensure_csrf_cookie
@require_http_methods(['GET'])
def get_csrf_token(request):
    '''GET CSRF token'''
    return JsonResponse({
        'token': get_token(request)
    })


@require_http_methods(['POST'])
def staff_login(request):
    '''Login para Staff'''
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_staff:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('admin:index')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Acesso negado: Usuário não permitido.'
                }, status=403)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Usuário ou senha inválidos.'
            }, status=401)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
