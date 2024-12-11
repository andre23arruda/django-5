from django.urls import path
from .views import calendar_plantoes, create_plantoes, see_escala, see_all_escalas

app_name = 'escala_de_plantao'

urlpatterns = [
    path('<int:escala_id>/criar-plantoes', create_plantoes, name='create_plantoes'),
    path('<int:escala_id>/ver-escala', see_escala, name='see_escala'),
    path('<int:escala_id>/ver-escala-meses', see_all_escalas, name='see_all_escalas'),
    path('<int:escala_id>/calendario', calendar_plantoes, name='calendar_plantoes'),
]