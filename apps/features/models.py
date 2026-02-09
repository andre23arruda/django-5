from django.db import models


class PodioDigitalFeaturePlanilha(models.Model):
    class Meta:
        verbose_name = 'Exportar Planilha'
        verbose_name_plural = 'Exportar Planilha'


class PodioDigitalFeatureLink(models.Model):
    class Meta:
        verbose_name = 'Link de Inscrição'
        verbose_name_plural = 'Link de Inscrição'


class PodioDigitalOpenGames(models.Model):
    class Meta:
        verbose_name = 'Criar jogos manualmente'
        verbose_name_plural = 'Criar jogos manualmente'


# class PodioDigitalFeatureQrCode(models.Model):
#     class Meta:
#         verbose_name = 'QR Code'
#         verbose_name_plural = 'QR Code'
