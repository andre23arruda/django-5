# Generated by Django 5.1.3 on 2025-03-05 12:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escala_de_plantao', '0006_alter_feriadopontofacultativo_ano'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='escala',
            name='plantonistas',
        ),
        migrations.CreateModel(
            name='OrdemPlantonista',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordem_na_lista', models.IntegerField()),
                ('escala', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='escala_de_plantao.escala', verbose_name='Escala')),
                ('plantonista', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='escala_de_plantao.plantonista')),
            ],
        ),
    ]
