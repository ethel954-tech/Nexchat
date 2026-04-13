from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.shortcuts import render
from django.utils.translation import gettext as _

from .models import User, Contact, StatusPrivacySetting
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .services.contact_sync import manual_contact_entry, sync_contacts_for_user


def register_page(request):
    return render(request, 'userapp/register.html')


def login_page(request):
    return render(request, 'userapp/login.html')


def profile_page(request):
    return render(request, 'userapp/profile.html')


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user.
    Expected input: {"username": "user", "email": "user@test.com", "password": "password123", "password2": "password123"}
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        sync_contacts_for_user(user)
        return Response(
            {
                'message': 'User created successfully',
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            },
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return token.
    Expected input: {"username": "user", "password": "password123"}
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    'message': 'Login successful',
                    'token': token.key,
                    'user_id': user.id,
                    'username': user.username
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by deleting their token.
    """
    request.user.auth_token.delete()
    return Response(
        {'message': 'Logout successful'},
        status=status.HTTP_200_OK
    )


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Retrieve or update the authenticated user's profile.
    """
    if request.method in ['PUT', 'PATCH']:
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            changed_phone = 'phone_number' in serializer.validated_data
            user = serializer.save()
            if changed_phone:
                sync_contacts_for_user(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


def _contact_payload(entry: Contact):
    target = entry.contact_user
    username = target.username if target else (entry.display_name or entry.phone_number)
    status_msg = target.status if target else None
    profile_picture = target.profile_picture.url if target and target.profile_picture else None
    return {
        'id': target.id if target else None,
        'username': username,
        'display_name': entry.display_name or username,
        'phone_number': entry.phone_number,
        'status': status_msg,
        'profile_picture': profile_picture,
        'is_mutual': entry.is_mutual,
    }


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def contacts(request):
    """
    GET: return mutual contacts.
    POST: add a contact by phone number (simulated sync entry).
    """
    if request.method == 'POST':
        phone_number = (request.data.get('phone_number') or '').strip()
        display_name = (request.data.get('display_name') or '').strip()
        if not phone_number:
            return Response({'error': _('Phone number is required.')}, status=status.HTTP_400_BAD_REQUEST)
        try:
            entry = manual_contact_entry(request.user, phone_number, display_name)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_contact_payload(entry), status=status.HTTP_201_CREATED)

    entries = (
        Contact.objects.filter(owner=request.user, is_mutual=True, contact_user__isnull=False)
        .select_related('contact_user')
        .order_by('display_name')
    )
    invite_link = f"{request.build_absolute_uri('/user/register-page/')}?ref={request.user.id}"
    data = [_contact_payload(entry) for entry in entries]
    return Response(
        {
            'contacts': data,
            'count': len(data),
            'invite_link': invite_link,
            'user_id': request.user.id,
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_contacts(request):
    """
    Trigger a manual sync of stored phone numbers against registered users.
    """
    sync_contacts_for_user(request.user)
    return Response({'message': 'Contacts refreshed.'}, status=status.HTTP_200_OK)


def _get_status_privacy(user):
    privacy, _ = StatusPrivacySetting.objects.get_or_create(user=user)
    return privacy


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def status_privacy_settings(request):
    privacy = _get_status_privacy(request.user)
    if request.method == 'PUT':
        visibility = request.data.get('visibility', StatusPrivacySetting.VISIBILITY_ALL)
        valid_values = {choice[0] for choice in StatusPrivacySetting.VISIBILITY_CHOICES}
        if visibility not in valid_values:
            return Response({'error': _('Invalid visibility option.')}, status=status.HTTP_400_BAD_REQUEST)
        privacy.visibility = visibility
        privacy.save(update_fields=['visibility'])
        excluded_ids = request.data.get('excluded_user_ids', [])
        if visibility == StatusPrivacySetting.VISIBILITY_CUSTOM:
            users = User.objects.filter(id__in=excluded_ids)
            privacy.excluded_users.set(users)
        else:
            privacy.excluded_users.clear()
        privacy.refresh_from_db()

    excluded = list(privacy.excluded_users.values_list('id', flat=True))
    return Response(
        {
            'visibility': privacy.visibility,
            'excluded_user_ids': excluded,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request, user_id):
    """
    Return public profile data for a given user.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': _('User not found.')}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
