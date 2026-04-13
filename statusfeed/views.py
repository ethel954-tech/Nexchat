from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Status
from userapp.models import Contact, StatusPrivacySetting


def _status_to_dict(status_obj):
    return {
        'id': status_obj.id,
        'user_id': status_obj.user_id,
        'username': status_obj.user.username,
        'profile_picture': status_obj.user.profile_picture.url if status_obj.user.profile_picture else None,
        'text': status_obj.text,
        'media_url': status_obj.media.url if status_obj.media else None,
        'created_at': status_obj.created_at,
    }


def _privacy_info(user, cache):
    if user_id := getattr(user, 'id', None):
        if user_id in cache:
            return cache[user_id]
    privacy = getattr(user, 'status_privacy', None)
    if not privacy:
        cache[user.id] = {
            'visibility': StatusPrivacySetting.VISIBILITY_ALL,
            'excluded': set(),
        }
        return cache[user.id]
    cache[user.id] = {
        'visibility': privacy.visibility,
        'excluded': set(privacy.excluded_users.values_list('id', flat=True)),
    }
    return cache[user.id]


def _can_view_status(status_obj, viewer_id, contact_owner_ids, privacy_cache):
    if status_obj.user_id == viewer_id:
        return True
    privacy = _privacy_info(status_obj.user, privacy_cache)
    visibility = privacy['visibility']
    if visibility == StatusPrivacySetting.VISIBILITY_CONTACTS:
        return status_obj.user_id in contact_owner_ids
    if visibility == StatusPrivacySetting.VISIBILITY_CUSTOM:
        return viewer_id not in privacy['excluded']
    return True


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_statuses(request):
    """
    Return statuses from the last 24 hours that the viewer is allowed to see.
    """
    cutoff = timezone.now() - timedelta(hours=24)
    statuses = (
        Status.objects.filter(created_at__gte=cutoff)
        .select_related('user', 'user__status_privacy')
        .prefetch_related('user__status_privacy__excluded_users')
    )
    owner_ids = {status_obj.user_id for status_obj in statuses if status_obj.user_id != request.user.id}
    contact_owner_ids = set()
    if owner_ids:
        contact_owner_ids = set(
            Contact.objects.filter(owner_id__in=owner_ids, contact_user=request.user, is_mutual=True)
            .values_list('owner_id', flat=True)
        )
    privacy_cache = {}
    visible_statuses = [
        status_obj for status_obj in statuses
        if _can_view_status(status_obj, request.user.id, contact_owner_ids, privacy_cache)
    ]
    data = [_status_to_dict(status_obj) for status_obj in visible_statuses]
    return Response({'statuses': data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_statuses(request):
    statuses = Status.objects.filter(user=request.user).order_by('-created_at')
    data = [_status_to_dict(status_obj) for status_obj in statuses]
    return Response({'statuses': data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_status(request):
    """
    Accept text (either `text` or `content`) and optional media file (either `media` or `file`).
    """
    text = request.data.get('text', '').strip() or request.data.get('content', '').strip()
    media_file = request.FILES.get('media') or request.FILES.get('file')

    if not text and media_file is None:
        return Response(
            {'error': 'Provide text or media for a status'},
            status=status.HTTP_400_BAD_REQUEST
        )

    status_obj = Status.objects.create(
        user=request.user,
        text=text,
        media=media_file,
    )

    return Response(_status_to_dict(status_obj), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def status_detail(request, status_id):
    try:
        status_obj = Status.objects.select_related('user', 'user__status_privacy').prefetch_related(
            'user__status_privacy__excluded_users'
        ).get(id=status_id)
    except Status.DoesNotExist:
        return Response({'error': 'Status not found'}, status=status.HTTP_404_NOT_FOUND)

    contact_owner_ids = set()
    if status_obj.user_id != request.user.id:
        contact_owner_ids = set(
            Contact.objects.filter(owner=status_obj.user, contact_user=request.user, is_mutual=True)
            .values_list('owner_id', flat=True)
        )
    if not _can_view_status(status_obj, request.user.id, contact_owner_ids, {}):
        return Response({'error': 'Status not available'}, status=status.HTTP_403_FORBIDDEN)

    return Response(_status_to_dict(status_obj), status=status.HTTP_200_OK)
