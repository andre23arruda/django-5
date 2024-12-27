from django.urls import path
from .views import reservar, confirmacao

app_name = 'aluguel_quadra'

urlpatterns = [
    path('reservar/', reservar, name='reservar'),
    path('confirmacao/<str:aluguel_id>/', confirmacao, name='confirmacao'),
]