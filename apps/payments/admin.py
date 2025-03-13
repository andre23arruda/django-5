from django.contrib import admin
from django.conf.locale.pt_BR import formats as pt_BR
from django.conf.locale.en import formats as en
from django.db import models

from .models import InputOutput

pt_BR.DATE_FORMAT = 'd/m/Y'
pt_BR.DATETIME_FORMAT = 'H:i:s - d/m/Y'
en.DATE_FORMAT = 'd/m/Y'
en.DATETIME_FORMAT = 'H:i:s - d/m/Y'


@admin.register(InputOutput)
class InputOutputRegister(admin.ModelAdmin):
    list_display = ('date', 'value', 'render_type', 'render_obs')
    list_display_links = ('date', 'value')
    list_filter = ('date', 'type')
    search_fields = ('obs',)
    change_list_template = 'admin/payments/inputoutput_change_list.html'
