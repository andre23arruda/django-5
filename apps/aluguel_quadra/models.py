from django.db import models
from shortuuid.django_fields import ShortUUIDField


class Quadra(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    TIPOS_QUADRA = [
        ('ABERTA', 'Aberta'),
        ('COBERTA', 'Coberta'),
    ]
    nome = models.CharField(max_length=100, verbose_name='Nome da Quadra')
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_QUADRA,
        default='ABERTA',
        verbose_name='Tipo de Quadra'
    )
    preco_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=60.0,
        verbose_name='Preço por Hora'
    )
    disponivel = models.BooleanField(default=True, verbose_name='Disponível')

    def __str__(self):
        return f'{self.nome} - {self.get_tipo_display()} (R${self.preco_hora}/hora)'

    class Meta:
        verbose_name = 'Quadra'
        verbose_name_plural = 'Quadras'


class Aluguel(models.Model):
    id = ShortUUIDField(length=8, max_length=40, primary_key=True)
    quadra = models.ForeignKey(
        Quadra,
        on_delete=models.CASCADE,
        related_name='alugueis',
        verbose_name='Quadra'
    )
    data = models.DateField(auto_now_add=True)
    inicio = models.TimeField(verbose_name='Início')
    fim = models.TimeField(verbose_name='Término')
    cliente_nome = models.CharField(max_length=100, verbose_name='Nome do Cliente')
    cliente_telefone = models.CharField(
        max_length=15,
        verbose_name='Telefone do Cliente',
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor Total'
    )
    pago = models.BooleanField(default=False, verbose_name='Pago')

    def __str__(self):
        return f'{ self.quadra.nome } - { self.cliente_nome }'

    def save(self, *args, **kwargs):
        duracao_horas = (self.fim.hour - self.inicio.hour ) + (self.fim.minute - self.inicio.minute) / 60
        self.valor_total = float(self.quadra.preco_hora) * duracao_horas
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Aluguel'
        verbose_name_plural = 'Aluguéis'