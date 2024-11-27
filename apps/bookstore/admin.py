from django.contrib import admin
from django.conf.locale.pt_BR import formats as pt_BR
from django.conf.locale.en import formats as en

from .models import Book, Genre

pt_BR.DATE_FORMAT = 'd/m/Y'
pt_BR.DATETIME_FORMAT = 'H:i:s - d/m/Y'
en.DATE_FORMAT = 'd/m/Y'
en.DATETIME_FORMAT = 'H:i:s - d/m/Y'


@admin.register(Book)
class BookRegister(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at',)
    list_display_links = ('id', 'title')
    search_fields = ('title',)
    autocomplete_fields = ['genre']


@admin.register(Genre)
class GenreRegister(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at',)
    list_display_links = ('id', 'name')
    search_fields = ('name',)
