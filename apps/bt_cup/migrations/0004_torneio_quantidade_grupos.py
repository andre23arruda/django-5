# Generated by Django 5.1.3 on 2025-02-16 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bt_cup', '0003_alter_torneio_ativo'),
    ]

    operations = [
        migrations.AddField(
            model_name='torneio',
            name='quantidade_grupos',
            field=models.IntegerField(choices=[(2, '2'), (4, '4'), (8, '8')], default=2),
        ),
    ]
