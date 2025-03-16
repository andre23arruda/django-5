from datetime import date
from django.core.management.base import BaseCommand
from faker import Faker
from payments.models import InputOutput


def create_payments():
    '''Cria pagamentos'''
    fake = Faker('pt_BR')
    date_end = date.today()
    date_start = date_end.replace(day=1, month=1, year=2024)
    for _ in range(1000):
        InputOutput.objects.create(
            date=fake.date_between_dates(date_start=date_start, date_end=date_end),
            value=fake.random_int(min=100, max=1000),
            type=fake.random_element(elements=('Entrada', 'Saída')),
            obs=f'Pagamento {fake.name()}'
        )
    print('Payments created successfully!')


class Command(BaseCommand):
    help = 'Create Payments'

    def handle(self, *args, **options):
        create_payments()
