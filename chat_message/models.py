from django.db import models
from django.conf import settings
from chats.models import Chat

User = settings.AUTH_USER_MODEL


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')

    content = models.TextField(blank=True)
    media = models.FileField(upload_to='messages/media/', blank=True, null=True)

    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender} -> {self.chat}"
