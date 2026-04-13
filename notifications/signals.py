from django.db.models.signals import post_save
from django.dispatch import receiver
from chat_message.models import Message
from .models import Notification


@receiver(post_save, sender=Message)
def create_notification(sender, instance, created, **kwargs):
    """
    Create notifications for all chat participants except the sender
    when a message is posted.
    """
    if created:
        # Get all participants in the chat except the sender
        participants = instance.chat.participants.exclude(id=instance.sender.id)
        
        # Create a notification for each participant
        for participant in participants:
            Notification.objects.create(
                user=participant,
                message=instance
            )
