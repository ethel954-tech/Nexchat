from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    is_saved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat {self.id}"


class SavedMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_messages')
    title = models.CharField(max_length=160, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} saved note"


class Channel(models.Model):
    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_PRIVATE = 'private'
    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, 'Public'),
        (VISIBILITY_PRIVATE, 'Private'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=120)
    topic = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=7, choices=VISIBILITY_CHOICES, default=VISIBILITY_PUBLIC)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('owner', 'name')

    def __str__(self):
        return f"{self.name} ({self.owner.username})"
