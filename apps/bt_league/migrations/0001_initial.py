# Generated by Django 5.1.3 on 2024-12-03 22:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Jogador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('telefone', models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                'verbose_name': 'Jogador',
                'verbose_name_plural': 'Jogadores',
            },
        ),
        migrations.CreateModel(
            name='Torneio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('data', models.DateField()),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('ativo', models.BooleanField(default=True)),
                ('criado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('jogadores', models.ManyToManyField(to='bt_league.jogador')),
            ],
        ),
        migrations.CreateModel(
            name='Jogo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('placar_dupla1', models.IntegerField(blank=True, null=True, verbose_name='')),
                ('placar_dupla2', models.IntegerField(blank=True, null=True, verbose_name='')),
                ('concluido', models.BooleanField(default=False)),
                ('dupla1_jogador1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dupla1_jogador1', to='bt_league.jogador')),
                ('dupla1_jogador2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dupla1_jogador2', to='bt_league.jogador')),
                ('dupla2_jogador1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dupla2_jogador1', to='bt_league.jogador')),
                ('dupla2_jogador2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dupla2_jogador2', to='bt_league.jogador')),
                ('torneio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bt_league.torneio')),
            ],
        ),
    ]
