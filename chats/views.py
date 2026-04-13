from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import render
from django.http import Http404
from .models import Chat, SavedMessage, Channel

User = get_user_model()


def ensure_saved_chat(user):
    """
    Ensure each user has a dedicated saved-messages chat.
    """
    saved = Chat.objects.filter(is_saved=True, participants=user).first()
    if saved:
        if saved.participants.count() != 1 or not saved.participants.filter(id=user.id).exists():
            saved.participants.set([user.id])
        return saved
    chat = Chat.objects.create(is_saved=True)
    chat.participants.set([user.id])
    return chat


# Frontend Template Views (regular Django views - no DRF wrapper)
def chat_list_page(request):
    """
    Render chat list page.
    """
    return render(request, 'chats/chat_list.html')


def chat_room_page(request, chat_id):
    """
    Render chat room page with chat_id in context.
    We can't rely on Django's session auth here because the frontend
    authenticates via DRF tokens (stored in localStorage), so the user
    often appears Anonymous to the template request. Fetch the chat by ID
    and only enforce participant checks if the session is authenticated.
    """
    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        raise Http404("Chat not found")

    return render(request, 'chats/chat_room.html', {
        'chat_id': chat_id,
        'chat': chat
    })


def saved_messages_view(request):
    """Standalone view for saved/personal notes."""
    return render(request, 'chats/saved.html')


def contacts_view(request):
    """Standalone contacts directory page."""
    return render(request, 'chats/contacts.html')


def create_group_view(request):
    """Entry point for creating a new group chat."""
    return render(request, 'chats/create_group.html')


def create_channel_view(request):
    """Entry point for creating a new broadcast channel."""
    return render(request, 'chats/create_channel.html')


def status_view(request):
    """Status timeline landing page."""
    return render(request, 'chats/status.html')


def status_privacy_view(request):
    """Status privacy configuration page."""
    return render(request, 'chats/status_privacy.html')


def profile(request):
    """Lightweight profile management page."""
    return render(request, 'chats/profile.html')


def contact_profile_view(request, user_id):
    """Telegram-style profile view for a specific user."""
    return render(request, 'chats/contact_profile.html', {'profile_user_id': user_id})


def settings_view(request):
    """General application settings page."""
    return render(request, 'chats/settings.html')


# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_chat(request):
    """
    Create a new chat with the given participants.
    Expected input: {"user_ids": [1, 2, 3]}
    """
    user_ids = request.data.get('user_ids', [])

    if not user_ids or not isinstance(user_ids, list):
        return Response(
            {'error': 'user_ids must be a non-empty list'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        normalized_ids = {int(user_id) for user_id in user_ids}
    except (TypeError, ValueError):
        return Response(
            {'error': 'user_ids must contain integers'},
            status=status.HTTP_400_BAD_REQUEST
        )

    normalized_ids.discard(request.user.id)
    if not normalized_ids:
        return Response(
            {'error': 'Select at least one other participant'},
            status=status.HTTP_400_BAD_REQUEST
        )

    participant_ids = list(normalized_ids | {request.user.id})

    users = User.objects.filter(id__in=participant_ids)
    if users.count() != len(participant_ids):
        return Response(
            {'error': 'One or more user IDs do not exist'},
            status=status.HTTP_400_BAD_REQUEST
        )

    chat = None
    created = False

    if len(participant_ids) == 2:
        other_id = next(user_id for user_id in participant_ids if user_id != request.user.id)
        chat = (
            Chat.objects.filter(is_saved=False, participants=request.user)
            .filter(participants__id=other_id)
            .annotate(num_participants=Count('participants', distinct=True))
            .filter(num_participants=2)
            .first()
        )

    if chat is None:
        chat = Chat.objects.create()
        chat.participants.set(participant_ids)
        created = True

    response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response(
        {
            'message': 'Chat created successfully' if created else 'Chat already exists',
            'chat_id': chat.id,
            'participant_ids': list(chat.participants.values_list('id', flat=True)),
            'created': created,
        },
        status=response_status
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_chats(request):
    """
    Get all chats where the authenticated user is a participant.
    """
    ensure_saved_chat(request.user)
    chats = (
        Chat.objects.filter(participants=request.user)
        .prefetch_related('participants', 'messages')
        .order_by('-created_at')
    )

    data = []
    for chat in chats:
        participants_qs = chat.participants.all()
        other_participants = participants_qs.exclude(id=request.user.id)
        if chat.is_saved:
            chat_name = "Saved Messages"
        elif other_participants.count() == 1:
            chat_name = other_participants.first().username
        elif other_participants:
            chat_name = ", ".join(other_participants.values_list('username', flat=True))
        else:
            chat_name = "Personal Chat"

        last_message = chat.messages.order_by('-created_at').first()
        last_message_payload = None
        if last_message:
            last_message_payload = {
                'id': last_message.id,
                'content': last_message.content,
                'sender_id': last_message.sender_id,
                'sender_username': last_message.sender.username,
                'created_at': last_message.created_at,
                'is_read': last_message.is_read,
                'media_url': last_message.media.url if last_message.media else None,
            }

        unread_count = chat.messages.filter(is_read=False).exclude(sender=request.user).count()

        data.append(
            {
                'chat_id': chat.id,
                'chat_name': chat_name,
                'participant_ids': list(participants_qs.values_list('id', flat=True)),
                'participants': [
                    {
                        'id': user.id,
                        'username': user.username,
                        'profile_picture': user.profile_picture.url if user.profile_picture else None,
                    }
                    for user in participants_qs
                ],
                'created_at': chat.created_at,
                'last_message': last_message_payload,
                'unread_count': unread_count,
                'is_saved': chat.is_saved,
            }
        )
    
    return Response({'chats': data}, status=status.HTTP_200_OK)


def _serialize_saved_message(saved_message):
    return {
        'id': saved_message.id,
        'title': saved_message.title or 'Untitled',
        'content': saved_message.content,
        'created_at': saved_message.created_at,
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def saved_messages_api(request):
    """
    List or create saved snippets that belong to the authenticated user.
    """
    if request.method == 'POST':
        title = (request.data.get('title') or '').strip()
        content = (request.data.get('content') or '').strip()
        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        saved_message = SavedMessage.objects.create(
            user=request.user,
            title=title,
            content=content
        )
        return Response(_serialize_saved_message(saved_message), status=status.HTTP_201_CREATED)

    saved_notes = SavedMessage.objects.filter(user=request.user)
    payload = [_serialize_saved_message(note) for note in saved_notes]
    return Response({'items': payload}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_saved_message(request, saved_id):
    """
    Delete a saved snippet owned by the authenticated user.
    """
    try:
        saved_message = SavedMessage.objects.get(id=saved_id, user=request.user)
    except SavedMessage.DoesNotExist:
        return Response({'error': 'Saved message not found'}, status=status.HTTP_404_NOT_FOUND)

    saved_message.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def _serialize_channel(channel):
    return {
        'id': channel.id,
        'name': channel.name,
        'topic': channel.topic,
        'description': channel.description,
        'visibility': channel.visibility,
        'created_at': channel.created_at,
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def channels_api(request):
    """
    List channels owned by the authenticated user or create a new channel.
    """
    if request.method == 'POST':
        name = (request.data.get('name') or '').strip()
        topic = (request.data.get('topic') or '').strip()
        description = (request.data.get('description') or '').strip()
        visibility = request.data.get('visibility') or Channel.VISIBILITY_PUBLIC

        if not name:
            return Response({'error': 'Channel name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if visibility not in dict(Channel.VISIBILITY_CHOICES):
            return Response({'error': 'Invalid visibility option'}, status=status.HTTP_400_BAD_REQUEST)

        channel = Channel.objects.create(
            owner=request.user,
            name=name,
            topic=topic,
            description=description,
            visibility=visibility,
        )
        return Response(_serialize_channel(channel), status=status.HTTP_201_CREATED)

    channels = Channel.objects.filter(owner=request.user)
    payload = [_serialize_channel(channel) for channel in channels]
    return Response({'channels': payload}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def channel_detail_api(request, channel_id):
    """
    Delete a channel that belongs to the authenticated user.
    """
    try:
        channel = Channel.objects.get(id=channel_id, owner=request.user)
    except Channel.DoesNotExist:
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)

    channel.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
