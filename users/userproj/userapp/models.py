from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, default='Hey there! I am using this app.')
    last_seen = models.DateTimeField(blank=True, null=True)

# Privacy settings
    EVERYONE = 'everyone'
    NOBODY = 'nobody'
    LAST_SEEN_CHOICES = [ 
        (EVERYONE, 'Everyone'),
        (NOBODY, 'Nobody'),
    ]
    last_seen_privacy = models.CharField(max_length=10, choices=LAST_SEEN_CHOICES, default=EVERYONE)
    read_receipts = models.BooleanField(default=True)
    blocked_users = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='blocked_by')
    def __str__(self):
        return self.username
