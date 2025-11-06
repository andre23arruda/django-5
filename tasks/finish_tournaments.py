import django, os
from datetime import date, timedelta
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from cup.models import Torneio as TorneioCup
from bt_league.models import Torneio as TorneioLeague


def delete_empty_tournaments():
    '''Deleta torneios vazios.'''
    torneios_cup = TorneioCup.objects.filter(ativo=False)
    for torneio in torneios_cup:
        sem_duplas = torneio.duplas.count() == 0
        sem_jogos = torneio.jogo_set.count() == 0
        if sem_duplas or sem_jogos:
            torneio.delete()
    torneios_league = TorneioLeague.objects.filter(ativo=False)
    for torneio in torneios_league:
        sem_duplas = torneio.jogadores.count() == 0
        sem_jogos = torneio.jogo_set.count() == 0
        if sem_duplas or sem_jogos:
            torneio.delete()
    print('Torneios vazios deletados com sucesso!')


def finish_tournaments():
    '''Finaliza torneios que estiverem com a data menor que a data atual.'''
    limit_date = date.today() - timedelta(days=3)
    TorneioCup.objects.filter(data__lt=limit_date).update(ativo=False)
    TorneioLeague.objects.filter(data__lt=limit_date).update(ativo=False)
    print('Torneios finalizados com sucesso!')


if __name__ == '__main__':
    finish_tournaments()
    delete_empty_tournaments()
