# Generated by Django 5.1.3 on 2025-01-07 18:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escala_de_plantao', '0005_alter_feriadopontofacultativo_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feriadopontofacultativo',
            name='ano',
            field=models.IntegerField(default=2025, verbose_name='Ano'),
        ),
    ]
