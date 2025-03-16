import datetime, locale
from django.contrib import admin
from django.conf.locale.pt_BR import formats as pt_BR
from django.conf.locale.en import formats as en
from django.db import models
from .models import InputOutput

locale.setlocale(locale.LC_MONETARY, 'pt_BR.UTF-8')

pt_BR.DATE_FORMAT = 'd/m/Y'
pt_BR.DATETIME_FORMAT = 'H:i:s - d/m/Y'
en.DATE_FORMAT = 'd/m/Y'
en.DATETIME_FORMAT = 'H:i:s - d/m/Y'


def get_period(date_str: str) -> str:
    today = datetime.date.today()
    this_week = today - datetime.timedelta(days=7)
    this_month = today.replace(day=1)
    this_year = today.replace(month=1, day=1)
    if date_str == today.strftime('%Y-%m-%d'):
        return 'Hoje'
    elif date_str == this_week.strftime('%Y-%m-%d'):
        return 'Últimos 7 dias'
    elif date_str == this_month.strftime('%Y-%m-%d'):
        return 'Este mês'
    elif date_str == this_year.strftime('%Y-%m-%d'):
        return 'Este ano'
    return 'Data'


@admin.register(InputOutput)
class InputOutputRegister(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('date', 'value', 'render_type', 'render_obs')
    list_display_links = ('date', 'value')
    list_per_page = 30
    list_filter = ['date', 'type']
    search_fields = ('obs',)
    change_list_template = 'admin/payments/inputoutput_change_list.html'

    def changelist_view(self, request, extra_context=None):
        query_params = request.GET
        day = query_params.get('date__day')
        month = query_params.get('date__month')
        year = query_params.get('date__year')
        date__gte = query_params.get('date__gte')
        type__exact = query_params.get('type__exact', '')
        obs = query_params.get('q', '')
        queryset = self.get_queryset(request)
        qs_filtered = queryset

        if date__gte:
            queryset = queryset.filter(date__gte=date__gte)

        if year and month and day:
            qs_filtered = queryset.filter(
                date__year=year,
                date__month=month,
                date__day=day,
                type__contains=type__exact,
                obs__icontains=obs
            )
        elif year and month:
            qs_filtered = queryset.filter(
                date__year=year,
                date__month=month,
                type__contains=type__exact,
                obs__icontains=obs
            )
        elif year:
            qs_filtered = queryset.filter(
                date__year=year,
                type__contains=type__exact,
                obs__icontains=obs
            )

        total = qs_filtered.aggregate(
            total_value=models.Sum(
                models.Case(
                    models.When(type='Entrada', then=models.F('value')),
                    models.When(type='Saída', then=-models.F('value')),
                    default=0,
                    output_field=models.DecimalField(),
                )
            )
        )['total_value'] or 0
        total = locale.currency(total, grouping=True).replace('R$', '').replace(' ', '')
        extra_context = extra_context or {}
        extra_context['total_value'] = total

        extra_context['period'] = 'Data'
        if date__gte:
            extra_context['period'] = get_period(date__gte)

        return super().changelist_view(request, extra_context)
