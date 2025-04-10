# Generated by Django 5.1.3 on 2025-03-05 12:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escala_de_plantao', '0007_remove_escala_plantonistas_ordemplantonista'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ordemplantonista',
            options={'verbose_name': 'Plantonista', 'verbose_name_plural': 'Plantonistas'},
        ),
        migrations.RemoveField(
            model_name='plantonista',
            name='ordem_na_lista',
        ),
        migrations.AlterField(
            model_name='ordemplantonista',
            name='escala',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plantonistas', to='escala_de_plantao.escala', verbose_name='Escala'),
        ),
    ]
