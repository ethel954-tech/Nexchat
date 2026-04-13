from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from chats.models import Chat
from .models import Message


def serialize_message(message):
    return {
        'message_id': message.id,
        'sender_id': message.sender.id,
        'sender_username': message.sender.username,
        'chat_id': message.chat.id,
        'content': message.content,
        'media_url': message.media.url if message.media else None,
        'created_at': message.created_at,
        'is_read': message.is_read,
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    Send a message to a chat.
    Expected input: {"chat_id": 1, "content": "Hello"}
    """
    chat_id = request.data.get('chat_id')
    content = request.data.get('content', '').strip()
    
    if not chat_id or not content:
        return Response(
            {'error': 'chat_id and content are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return Response(
            {'error': 'Chat not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user is a participant
    if not chat.participants.filter(id=request.user.id).exists():
        return Response(
            {'error': 'You are not a participant in this chat'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Create the message
    message = Message.objects.create(
        sender=request.user,
        chat=chat,
        content=content
    )
    
    return Response(serialize_message(message), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_messages(request, chat_id):
    """
    Get all messages in a chat.
    Only participants can view messages.
    """
    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return Response(
            {'error': 'Chat not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user is a participant
    if not chat.participants.filter(id=request.user.id).exists():
        return Response(
            {'error': 'You are not a participant in this chat'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    messages = Message.objects.filter(chat=chat, is_deleted=False)
    
    data = [serialize_message(msg) for msg in messages]
    
    return Response({'messages': data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_as_read(request, chat_id):
    """
    Mark all messages in a chat as read for the current user.
    """
    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return Response(
            {'error': 'Chat not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user is a participant
    if not chat.participants.filter(id=request.user.id).exists():
        return Response(
            {'error': 'You are not a participant in this chat'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Mark all messages as read
    messages = Message.objects.filter(chat=chat, is_deleted=False)
    updated_count = messages.update(is_read=True)
    
    return Response(
        {'message': f'{updated_count} messages marked as read'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_message_media(request):
    """
    Upload an image (or media) into a chat conversation.
    """
    chat_id = request.data.get('chat_id')
    media_file = request.FILES.get('image') or request.FILES.get('media')

    if not chat_id or media_file is None:
        return Response(
            {'error': 'chat_id and media file are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)

    if not chat.participants.filter(id=request.user.id).exists():
        return Response({'error': 'You are not a participant in this chat'}, status=status.HTTP_403_FORBIDDEN)

    message = Message.objects.create(
        sender=request.user,
        chat=chat,
        media=media_file,
        content=request.data.get('caption', '').strip()
    )

    return Response(serialize_message(message), status=status.HTTP_201_CREATED)
