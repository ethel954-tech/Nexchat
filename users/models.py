from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    status = models.CharField(max_length=255, blank=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username