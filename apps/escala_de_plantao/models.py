from datetime import date, timedelta
from django.db import models
from django.utils import timezone


TURNO_CHOICES = [
    (1, 'Manhã'),
    (2, 'Noite'),
]

def is_holliday(date):
    '''Função para verificar se uma data é feriado'''
    # Lista de feriados fixos (exemplo)
    hollidays = [
        (1, 1),   # Ano Novo
        (4, 21),  # Tiradentes
        (5, 1),   # Dia do Trabalho
        (9, 7),   # Independência do Brasil
        (10, 12), # Dia das Crianças
        (11, 2),  # Finados
        (11, 15), # Proclamação da República
        (12, 25)  # Natal
    ]
    custom_hollidays = list(FeriadoPontoFacultativo.objects.filter(ano=date.year).values_list('dia', 'mes'))

    # Verifica se a data coincide com algum feriado
    if (date.month, date.day) in hollidays + custom_hollidays:
        return True

    return False


class FeriadoPontoFacultativo(models.Model):
    nome = models.CharField(max_length=100)
    dia = models.IntegerField()
    mes = models.IntegerField()
    ano = models.IntegerField(default=timezone.now().year)

    class Meta:
        verbose_name = 'Feriado / Ponto facultativo'
        verbose_name_plural = 'Feriados / Pontos facultativos'

    def __str__(self):
        return self.nome + ' (' + str(self.dia) + '/' + str(self.mes) + '/' + str(self.ano) + ')'

    def data(self):
        return f'{self.dia}/{self.mes}/{self.ano}'


class Plantonista(models.Model):
    nome = models.CharField(max_length=100)
    ordem_na_lista = models.IntegerField()
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    proximas_ferias = models.DateField(null=True, blank=True)
    dias_de_ferias = models.IntegerField(null=True, blank=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Plantonista'
        verbose_name_plural = 'Plantonistas'

    def __str__(self):
        return self.nome

    def online(self, date=None):
        if date:
            current_date = date
        else:
            current_date = timezone.now().date()
        if self.proximas_ferias and self.dias_de_ferias:
            return not(self.proximas_ferias <= current_date <= self.proximas_ferias + timezone.timedelta(days=self.dias_de_ferias))
        return True


class Escala(models.Model):
    nome = models.CharField(max_length=100)
    plantonistas = models.ManyToManyField(Plantonista, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    def plantonista_online(self, indice_inicial: int, date=None):
        '''Encontra o próximo plantonista disponível a partir do índice inicial.'''
        plantonistas = list(self.plantonistas.all())
        total_plantonistas = len(plantonistas)
        for i in range(total_plantonistas):
            # Calcula o índice do plantonista, considerando a rotatividade
            indice = (indice_inicial + i) % total_plantonistas
            plantonista = plantonistas[indice]

            # Verifica se o plantonista está online (não está de férias)
            if plantonista.online(date):
                return plantonista, indice

        # Se nenhum plantonista estiver disponível
        return None, None

    def create_plantoes(self):
        # Define o mês atual e próximo mês
        today = timezone.now().date()
        first_day = today.replace(day=6)
        last_day = (first_day + timedelta(days=32)).replace(day=6)

        # Busca todos os plantonistas da escala ordenados por ordem_na_lista
        plantonistas = list(self.plantonistas.order_by('ordem_na_lista'))

        # Encontra o último plantão do mês anterior
        plantao_anterior = Plantao.objects.filter(escala=self).order_by('-data').first()

        # Define o índice inicial
        if plantao_anterior:
            # Encontra o índice do último plantonista
            index_plantonista = next(
                (i for i, plantonista in enumerate(plantonistas)
                if plantonista.id == plantao_anterior.plantonista_id),
                0
            )
            # Incrementa para começar no próximo plantonista
            index_plantonista = (index_plantonista + 1) % len(plantonistas)

            first_day = plantao_anterior.data
            last_day = (first_day + timedelta(days=32)).replace(day=6)
        else:
            # Se não houver plantão anterior, começa do primeiro plantonista
            index_plantonista = 0

        # Itera sobre cada dia do período
        current_day = first_day
        while current_day < last_day:
            # Verifica se é fim de semana ou feriado
            weekend = current_day.weekday() in [5, 6]  # 5 = sábado, 6 = domingo
            holliday = is_holliday(current_day)  # Função de verificação de feriado

            # Lógica para turnos
            if weekend or holliday:
                # Encontra plantonista para a manhã
                plantonista_manha, i = self.plantonista_online(index_plantonista, current_day)
                if plantonista_manha:
                    Plantao.objects.create(
                        escala=self,
                        plantonista=plantonista_manha,
                        turno=1,  # Manhã
                        data=current_day
                    )
                    # Incrementa o índice
                    index_plantonista = i + 1

            # Encontra plantonista para a noite
            plantonista_noite, i = self.plantonista_online(index_plantonista, current_day)
            if plantonista_noite:
                Plantao.objects.create(
                    escala=self,
                    plantonista=plantonista_noite,
                    turno=2,  # Noite
                    data=current_day
                )
                # Incrementa o índice
                index_plantonista = i + 1

            # Avança para o próximo dia
            current_day += timedelta(days=1)

        return True


class Plantao(models.Model):
    escala = models.ForeignKey(Escala, on_delete=models.CASCADE)
    plantonista = models.ForeignKey(Plantonista, on_delete=models.CASCADE)
    turno = models.IntegerField(choices=TURNO_CHOICES, default=2)
    data = models.DateField()

    class Meta:
        verbose_name = 'Plantão'
        verbose_name_plural = 'Plantões'

    def __str__(self):
        return f'{self.plantonista} ({self.data})'

    def done(self):
        return timezone.now().date() > self.data
