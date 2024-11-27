# from djongo import models
from django.db import models

from django.contrib.auth.models import User

class Genre(models.Model):
    created_at = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f'{ self.name }'

class Book(models.Model):
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    title = models.CharField(max_length=50)
    genre = models.ManyToManyField(Genre, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{ self.title }'