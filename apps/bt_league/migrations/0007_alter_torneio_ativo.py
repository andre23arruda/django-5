# Generated by Django 5.1.3 on 2024-12-31 01:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bt_league', '0006_jogo_quadra_torneio_quadras'),
    ]

    operations = [
        migrations.AlterField(
            model_name='torneio',
            name='ativo',
            field=models.BooleanField(default=True, verbose_name='Ativo'),
        ),
    ]
