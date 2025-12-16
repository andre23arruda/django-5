from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
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
