from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


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

    def save(self, *args, **kwargs):
        if self.phone_number:
            self.phone_number = ''.join(ch for ch in str(self.phone_number) if ch.isdigit())
        super().save(*args, **kwargs)


class Contact(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contact_entries'
    )
    contact_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appears_in_contacts'
    )
    phone_number = models.CharField(max_length=32)
    display_name = models.CharField(max_length=120, blank=True)
    is_mutual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('owner', 'phone_number')
        ordering = ['display_name']

    def __str__(self):
        return f"{self.owner.username} → {self.display_name or self.phone_number}"


class StatusPrivacySetting(models.Model):
    VISIBILITY_ALL = 'all'
    VISIBILITY_CONTACTS = 'contacts'
    VISIBILITY_CUSTOM = 'custom'
    VISIBILITY_CHOICES = [
        (VISIBILITY_ALL, 'Everyone'),
        (VISIBILITY_CONTACTS, 'My Contacts'),
        (VISIBILITY_CUSTOM, 'Everyone except...'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='status_privacy'
    )
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_ALL)
    excluded_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='status_privacy_exclusions'
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} status privacy"
