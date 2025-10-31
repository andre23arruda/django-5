import os, threading
from django.core.mail import send_mail, EmailMessage


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


def send_email_html(title: str, msg_html: str):
    '''Envio de email com HTML de forma assíncrona'''
    def send_async(title, msg_html):
        email = EmailMessage(
            subject=title,
            body=msg_html,
            from_email=os.getenv('DEFAULT_FROM_EMAIL'),
            to=[os.getenv('DEFAULT_FROM_EMAIL')],
        )
        email.content_subtype = 'html'
        email.send(fail_silently=True)

    thread = threading.Thread(target=send_async, args=(title, msg_html))
    thread.daemon = True
    thread.start()
