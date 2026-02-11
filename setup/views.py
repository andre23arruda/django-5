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
            msg_html = f'''
                <div style="border-style:solid; border-width:thin; border-color:#dadce0; border-radius:8px; padding:40px 20px; max-width: 550px; margin: 20px auto;" align="center">
                    <img src="{ os.environ.get('APP_LINK') }/logo-email.png" width="160" style="margin-bottom:16px; display: block;" alt="Pódio Digital">

                    <div style="font-family:'Google Sans',Roboto,RobotoDraft,Helvetica,Arial,sans-serif; border-bottom:thin solid #dadce0; color:rgba(0,0,0,0.87); line-height:32px; padding-bottom:24px; text-align:center; word-break:break-word">
                        <div style="font-size:24px">Verifique seu acesso</div>
                    </div>

                    <div style="font-family:Roboto-Regular,Helvetica,Arial,sans-serif; font-size:14px; color:rgba(0,0,0,0.87); line-height:20px; padding-top:20px; text-align:left">
                        Olá, <b>{user.username}</b>.
                        <br><br>
                        Recebemos uma solicitação de login para sua conta no painel do <b>Pódio Digital</b>.
                        Use este código para concluir a autenticação:

                        <div style="text-align:center; font-size:36px; margin:30px 0; line-height:44px; color:rgba(0,0,0,0.87); letter-spacing: 4px;">
                            <strong>{otp}</strong>
                        </div>

                        Este código expirará em <b>5 minutos</b>.
                        <br><br>
                        Se você não reconhece esta atividade ou não tentou fazer login, você pode ignorar este e-mail com segurança. Nenhuma alteração foi feita na sua conta.
                    </div>
                </div>
                <div style="text-align: center; font-family: Roboto,Arial,sans-serif; font-size: 11px; color: #70757a; margin-top: 15px;">
                    Este é um e-mail automático. Por favor, não responda.
                </div>
            '''
            send_email_html(
                title='Seu Código de Acesso - Pódio Digital',
                msg_html=msg_html,
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
