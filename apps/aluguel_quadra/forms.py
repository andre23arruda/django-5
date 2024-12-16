from datetime import date, datetime
from django import forms
from .models import Aluguel, Quadra


def round_time(delta=1):
    hour = datetime.now().hour
    result = datetime.now().replace(hour=hour+delta, minute=0, second=0, microsecond=0)
    return result.strftime('%H:%M')


def initial_time():
    hour = datetime.now().hour + 1
    next_hour = hour + 1
    return f'{hour}:00-{next_hour}:00'


class AgendamentoForm(forms.ModelForm):
    HORARIOS_CHOICES = [
        ('17:00-18:00', '17:00 - 18:00'),
        ('18:00-19:00', '18:00 - 19:00'),
        ('19:00-20:00', '19:00 - 20:00'),
        ('20:00-21:00', '20:00 - 21:00'),
        ('21:00-22:00', '21:00 - 22:00'),
        ('22:00-23:00', '22:00 - 23:00'),
    ]
    quadra = forms.ModelChoiceField(
        queryset=Quadra.objects.filter(disponivel=True),
        label='Selecione a Quadra',
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    horario = forms.ChoiceField(
        choices=HORARIOS_CHOICES,
        label='Selecione o Horário',
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial=initial_time()
    )
    cliente_nome = forms.CharField(
        max_length=100,
        label='Seu Nome Completo',
        widget=forms.TextInput(attrs={'class': 'form-control', 'required': True})
    )
    cliente_telefone = forms.CharField(
        max_length=15,
        label='Seu Telefone',
        widget=forms.TextInput(attrs={'type': 'tel', 'class': 'form-control', 'required': True, 'placeholder': '(XX) 9XXXX-XXXX'})
    )

    class Meta:
        model = Aluguel
        fields = ['quadra', 'cliente_nome', 'cliente_telefone']

    def clean(self):
        cleaned_data = super().clean()
        quadra = cleaned_data.get('quadra')
        horario = cleaned_data.get('horario')
        hora_inicio, hora_fim = horario.split('-')
        today = date.today()

        data_inicio = datetime.combine(
            today,
            datetime.strptime(hora_inicio, '%H:%M').time()
        )
        data_fim = datetime.combine(
            today,
            datetime.strptime(hora_fim, '%H:%M').time()
        )

        # Verifica se a data de início é anterior à data atual
        now = datetime.now()
        if data_inicio < now:
            raise forms.ValidationError('A data de início não pode ser no passado.')

        # Verifica se a data de término é posterior à data de início
        if data_fim <= data_inicio:
            raise forms.ValidationError('A data de término deve ser posterior à data de início.')

        # Verifica conflitos de agendamento
        conflitos = Aluguel.objects.filter(
            quadra=quadra,
            data=today,
            inicio__lte=data_inicio.time(),
            fim__gte=data_fim.time()
        )
        if conflitos.exists():
            raise forms.ValidationError('Já existe um agendamento para esta quadra neste horário.')

        cleaned_data['inicio'] = data_inicio.time()
        cleaned_data['fim'] = data_fim.time()
        return cleaned_data


    def save(self, commit=True):
        # Sobrescrevendo o método save para usar as datas processadas
        aluguel = super().save(commit=False)
        aluguel.inicio = self.cleaned_data['inicio']
        aluguel.fim = self.cleaned_data['fim']

        if commit:
            aluguel.save()
        return aluguel