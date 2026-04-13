from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Notification


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get all notifications for the authenticated user.
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    data = [
        {
            'id': notification.id,
            'message_id': notification.message.id,
            'chat_id': notification.message.chat.id,
            'sender_id': notification.message.sender.id,
            'content': notification.message.content,
            'is_read': notification.is_read,
            'created_at': notification.created_at
        }
        for notification in notifications
    ]
    
    return Response({'notifications': data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    """
    Mark a single notification as read.
    """
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if the notification belongs to the authenticated user
    if notification.user.id != request.user.id:
        return Response(
            {'error': 'You do not have permission to access this notification'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    notification.is_read = True
    notification.save()
    
    return Response(
        {'message': 'Notification marked as read'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_as_read(request):
    """
    Mark all notifications as read for the authenticated user.
    """
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    updated_count = notifications.update(is_read=True)
    
    return Response(
        {'message': f'{updated_count} notifications marked as read'},
        status=status.HTTP_200_OK
    )

