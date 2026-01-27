import os, threading
from django.core.mail import send_mail, EmailMessage
import logging
from telegram import Bot

logger = logging.getLogger(__name__)


def send_email(title: str, msg: str):
    '''Envio simples de email'''
    try:
        send_mail(
            subject=title,
            message=msg,
            from_email=os.getenv('DEFAULT_FROM_EMAIL'),
            recipient_list=[os.getenv('DEFAULT_FROM_EMAIL')],
            fail_silently=False,
        )
    except Exception as e:
        print(e)


def send_email_html(title: str, msg_html: str, to=None):
    '''Envio de email com HTML de forma assíncrona'''
    def send_async(title, msg_html):
        email = EmailMessage(
            subject=title,
            body=msg_html,
            from_email=os.getenv('DEFAULT_FROM_EMAIL'),
            to=[to or os.getenv('DEFAULT_FROM_EMAIL')],
        )
        email.content_subtype = 'html'
        email.send(fail_silently=True)

    thread = threading.Thread(target=send_async, args=(title, msg_html))
    thread.daemon = True
    thread.start()


def send_telegram_msg(torneio: object, link: str):
    '''Envio de email com HTML de forma assíncrona'''
    def send_async():
        try:
            telegram_msg = f'''
🏆 *Novo Torneio Criado!*

📝 *Nome:* {torneio.nome}

📅 *Data:* {torneio.data.strftime('%d/%m/%Y')}

👤 *Criado por:* {torneio.criado_por}

_Acesse o link para mais detalhes!_: [{link}]({link})
'''
            bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
            destino = os.getenv('TELEGRAM_CHAT_ID')
            bot.send_message(
                chat_id=destino,
                text=telegram_msg,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f'Erro ao enviar mensagem: {e}')

    thread = threading.Thread(target=send_async)
    thread.daemon = True
    thread.start()
