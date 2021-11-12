from django.db import models
from django.urls import reverse

class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=50)
    car_licence = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=12)

    def get_absolute_url(self):
        return reverse('Fuel:index')