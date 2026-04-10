from django.contrib.auth.models import AbstractUser
from django.db import models

class Vehicle(models.Model):
    name = models.CharField(max_length=100)
    battery_type = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=100)
class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)

class UploadedDataset(models.Model):
    file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name