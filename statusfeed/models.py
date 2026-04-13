from django.conf import settings
from django.db import models


class Status(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='statuses'
    )
    text = models.TextField(blank=True)
    media = models.FileField(upload_to='status/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} status"
