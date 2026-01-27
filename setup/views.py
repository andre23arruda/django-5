import json, os, random, string
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from utils.send_email import send_email_html


def generate_otp():
    '''Gera um código numérico de 6 dígitos.'''
    return ''.join(random.choices(string.digits, k=6))


@require_http_methods(['GET'])
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


@require_http_methods(['POST'])
def check_otp(request):
    '''Valida o código recebido e inicia a sessão oficial'''
    data = json.loads(request.body)
    user_id = data.get('user_id')
    otp_received = data.get('otp_code')
    cached_otp = cache.get(f'otp_user_{user_id}')

    if cached_otp and cached_otp == otp_received:
        try:
            user = User.objects.get(id=user_id)
            login(request, user)
            cache.delete(f'otp_user_{user_id}')
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('admin:index')
            })
        except User.DoesNotExist:
            return JsonResponse({'message': 'Usuário inválido.'}, status=400)

    return JsonResponse({'message': 'Código inválido ou expirado.'}, status=401)


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

        if user is not None and user.is_staff:
            otp = generate_otp()
            cache.set(f'otp_user_{user.id}', otp, timeout=300)
            send_email_html(
                title='Seu Código de Acesso - Pódio Digital',
                msg_html=f'''
                    Olá, <b>{user.username}</b>,
                    <br/>
                    Seu código de autenticação para acessar o painel do Pódio Digital:
                    <div style="text-align: center; font-size: 2rem; margin: 1rem 0; padding: 1rem; background-color: lightgray;">
                        <b>{otp}</b>
                    </div>
                    <i>Atenção: </i> Este código expira em 5 minutos.
                ''',
                to=user.email or os.getenv('DEFAULT_FROM_EMAIL')
            )
            return JsonResponse({
                'otp_required': True,
                'user_id': user.id,
                'message': 'Código enviado com sucesso.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Acesso negado: Usuário não permitido.'
            }, status=403)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Usuário ou senha inválidos.'
        }, status=401)
