from django.db import models

class Business(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=2, choices=[('KG', 'Кыргызстан')], default='KG')

    def __str__(self):
        return self.name

# Create your models here.
