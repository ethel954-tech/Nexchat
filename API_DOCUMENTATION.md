# Django Messaging REST API - Complete System Documentation

## System Overview

This document outlines the complete end-to-end messaging API system with authentication, chats, messages, and notifications.

---

## Architecture & Dependencies

### App Structure
```
config/
├── settings.py          # Auth: TokenAuthentication + 'rest_framework.authtoken'
├── urls.py              # Main URL router

userapp/                 # Authentication System
├── models.py            # User (Custom AbstractUser)
├── serializers.py       # RegisterSerializer, LoginSerializer, UserSerializer
├── views.py             # API: register, login, logout, profile
└── urls.py              # Routes: /user/auth/*

chats/                   # Chat Management System
├── models.py            # Chat (participants: M2M User)
├── views.py             # API: create_chat, get_user_chats
└── urls.py              # Routes: /chats/*

chat_message/            # Message System
├── models.py            # Message (sender FK User, chat FK Chat)
├── views.py             # API: send_message, get_chat_messages, mark_messages_as_read
└── urls.py              # Routes: /messages/*

notifications/           # Notification System
├── models.py            # Notification (user FK, message FK)
├── signals.py           # Auto-create notifications on Message.post_save
├── apps.py              # AppConfig with signals.ready()
├── views.py             # API: get_notifications, mark_as_read, read-all
└── urls.py              # Routes: /notifications/*
```

### Import Dependencies
```
userapp.models.User
    ↓
chats.models.Chat (contains M2M User)
    ↓
chat_message.models.Message (sender FK User, chat FK Chat)
    ↓
notifications.models.Notification (user FK User, message FK Message)
    ↓
notifications.signals (post_save signal on Message)
```

---

## Authentication Flow

### Step 1: Register User
**Endpoint:** `POST /user/auth/register/`
**Parameters:** `AllowAny`

```json
Request:
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!"
}

Response (201):
{
    "message": "User created successfully",
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com"
}
```

**Backend Flow:**
1. `userapp.views.register()` receives request
2. `RegisterSerializer` validates password matching
3. `User.objects.create_user()` hashes password (never stored as plaintext)
4. User created in database

---

### Step 2: Login User
**Endpoint:** `POST /user/auth/login/`
**Permissions:** `AllowAny`

```json
Request:
{
    "username": "john_doe",
    "password": "SecurePass123!"
}

Response (200):
{
    "message": "Login successful",
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 1,
    "username": "john_doe"
}
```

**Backend Flow:**
1. `userapp.views.login()` receives credentials
2. `LoginSerializer` validates input format
3. `django.contrib.auth.authenticate(username, password)` authenticates
4. `Token.objects.get_or_create(user=user)` creates/retrieves token
5. Token returned to client

---

### Step 3: Access Protected Endpoints
**All subsequent requests require TokenAuthentication**

```
Headers: Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Setting:** `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES = TokenAuthentication`

---

## Chat Flow

### Create Chat
**Endpoint:** `POST /chats/create/`
**Permissions:** `IsAuthenticated`

```json
Request:
{
    "user_ids": [2, 3]
}

Response (201):
{
    "message": "Chat created successfully",
    "chat_id": 1,
    "participant_ids": [1, 2, 3]
}
```

**Backend Flow:**
1. `chats.views.create_chat()` receives user_ids
2. `request.user` (authenticated) auto-added to participants
3. `Chat.objects.create()` creates chat
4. `chat.participants.set(user_ids)` adds all participants
5. Chat ID returned

**Database State:**
```
Chat table: id=1, created_at=now
Chat_User (M2M): chat_id=1, user_id=1,2,3
```

---

### Get User Chats
**Endpoint:** `GET /chats/`
**Permissions:** `IsAuthenticated`

```json
Response (200):
{
    "chats": [
        {
            "chat_id": 1,
            "participant_ids": [1, 2, 3],
            "created_at": "2026-03-31T10:30:00Z"
        }
    ]
}
```

**Backend Flow:**
1. `chats.views.get_user_chats()` queries chats
2. `Chat.objects.filter(participants=request.user)` filters only user's chats
3. Data serialized and returned

---

## Message Flow

### Send Message
**Endpoint:** `POST /messages/send/`
**Permissions:** `IsAuthenticated`

```json
Request:
{
    "chat_id": 1,
    "content": "Hello everyone!"
}

Response (201):
{
    "message_id": 1,
    "sender_id": 1,
    "chat_id": 1,
    "content": "Hello everyone!",
    "created_at": "2026-03-31T10:35:00Z",
    "is_read": false
}
```

**Backend Flow:**
1. `chat_message.views.send_message()` receives message data
2. Validates `chat_id` exists
3. Validates `request.user` is participant (using `chat.participants.filter()`)
4. `Message.objects.create()` creates message with:
   - `sender = request.user`
   - `chat = Chat`
   - `content = content`
   - `is_read = False`
   - `is_deleted = False`
   - `created_at = auto_now_add`

**Signal Triggers:**
```python
@receiver(post_save, sender=Message)
def create_notification(sender, instance, created, **kwargs):
    if created:
        # Get all participants except sender
        participants = instance.chat.participants.exclude(id=instance.sender.id)
        
        # Create notification for each
        for participant in participants:
            Notification.objects.create(
                user=participant,
                message=instance
            )
```

---

### Get Chat Messages
**Endpoint:** `GET /messages/<chat_id>/`
**Permissions:** `IsAuthenticated`

```json
Response (200):
{
    "messages": [
        {
            "message_id": 1,
            "sender_id": 1,
            "content": "Hello everyone!",
            "created_at": "2026-03-31T10:35:00Z",
            "is_read": true
        },
        {
            "message_id": 2,
            "sender_id": 2,
            "content": "Hi there!",
            "created_at": "2026-03-31T10:36:00Z",
            "is_read": false
        }
    ]
}
```

**Backend Flow:**
1. `chat_message.views.get_chat_messages()` receives chat_id
2. Validates chat exists
3. Validates `request.user` is participant
4. `Message.objects.filter(chat=chat, is_deleted=False)` retrieves messages
5. Messages serialized and returned (ordered by created_at)

---

### Mark Messages as Read
**Endpoint:** `POST /messages/read/<chat_id>/`
**Permissions:** `IsAuthenticated`

```json
Response (200):
{
    "message": "2 messages marked as read"
}
```

**Backend Flow:**
1. Chat validation and participant check
2. `Message.objects.filter(chat=chat).update(is_read=True)`
3. Count returned

---

## Notification Flow

### Auto-Generate Notifications
**Triggered by:** Message.post_save signal

**Flow:**
1. User A sends message to Chat 1 (participants: A, B, C)
2. `Message.objects.create()` triggers signal
3. `notifications.signals.create_notification()` runs
4. Creates 2 Notifications (for B and C, NOT for A)
5. Each notification linked to the message

**Database State:**
```
Notification table:
id  | user_id | message_id | is_read | created_at
1   | 2       | 1          | False   | 2026-03-31...
2   | 3       | 1          | False   | 2026-03-31...
```

---

### Get Notifications
**Endpoint:** `GET /notifications/`
**Permissions:** `IsAuthenticated`

```json
Response (200):
{
    "notifications": [
        {
            "id": 1,
            "message_id": 5,
            "chat_id": 2,
            "sender_id": 2,
            "content": "Hello everyone!",
            "is_read": false,
            "created_at": "2026-03-31T10:40:00Z"
        },
        {
            "id": 2,
            "message_id": 6,
            "chat_id": 2,
            "sender_id": 3,
            "content": "How are you?",
            "is_read": false,
            "created_at": "2026-03-31T10:41:00Z"
        }
    ]
}
```

**Backend Flow:**
1. `notifications.views.get_notifications()` filters
2. `Notification.objects.filter(user=request.user)` gets user's notifications
3. Each notification includes message details
4. Ordered by -created_at (newest first)

---

### Mark Notification as Read
**Endpoint:** `POST /notifications/read/<id>/`
**Permissions:** `IsAuthenticated`

```json
Response (200):
{
    "message": "Notification marked as read"
}
```

**Backend Flow:**
1. Get notification by id
2. Verify ownership: `notification.user == request.user`
3. Update `is_read = True`
4. Save to database

---

### Mark All as Read
**Endpoint:** `POST /notifications/read-all/`
**Permissions:** `IsAuthenticated`

```json
Response (200):
{
    "message": "5 notifications marked as read"
}
```

**Backend Flow:**
1. `Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)`
2. Return count of updated

---

## Complete End-to-End Workflow Example

### Scenario: User A sends message to User B and C

#### 1. User A Registers
```
POST /user/auth/register/
→ User A created, id=1
```

#### 2. User B and C Register
```
POST /user/auth/register/
→ User B created, id=2
→ User C created, id=3
```

#### 3. All Users Login
```
POST /user/auth/login/
→ User A gets token_a
→ User B gets token_b
→ User C gets token_c
```

#### 4. User A Creates Chat
```
POST /chats/create/
Headers: Authorization: Token token_a
Body: {"user_ids": [2, 3]}
→ Chat 1 created with participants [1, 2, 3]
```

#### 5. User A Sends Message
```
POST /messages/send/
Headers: Authorization: Token token_a
Body: {"chat_id": 1, "content": "Hello!"}
→ Message 1 created
→ Signal fires: post_save on Message
→ 2 Notifications created (for user_id 2 and 3)
```

#### 6. User B Receives Notification
```
GET /notifications/
Headers: Authorization: Token token_b
→ Returns notification for message from User A
```

#### 7. User B Views Chat Messages
```
GET /messages/1/
Headers: Authorization: Token token_b
→ Returns all messages in Chat 1
```

#### 8. User B Marks Notification as Read
```
POST /notifications/read/<notification_id>/
Headers: Authorization: Token token_b
→ Notification.is_read = True
```

---

## Security & Validation

### Authentication
- Token-based (stateless)
- Stored in `authtoken_token` table
- Passwords hashed with Django's default hasher

### Authorization
- All endpoints require `IsAuthenticated` (except register/login)
- Chat participation validated before message send/view
- Users can only see their own notifications

### Validation
- Chat exists before sending message
- User is participant before accessing chat
- Notification belongs to user before modifying
- All inputs validated by serializers

---

## Main URL Configuration

**File:** `config/urls.py`

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('userapp.urls')),       # Auth endpoints
    path('messages/', include('chat_message.urls')), # Message endpoints
    path('notifications/', include('notifications.urls')), # Notification endpoints
    path('chats/', include('chats.urls')),        # Chat endpoints
]
```

---

## Settings Configuration

**File:** `config/settings.py`

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',  # ← Token authentication
    'userapp',
    'chat_message',
    'notifications',
    'chats',
]

AUTH_USER_MODEL = 'userapp.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
```

---

## Deployment Checklist

- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Test auth: POST /user/auth/register/
- [ ] Test chat creation: POST /chats/create/
- [ ] Test message sending: POST /messages/send/
- [ ] Verify signals work: Check notifications created
- [ ] Test token authentication on all endpoints

---

## Database Schema Summary

```
User (userapp_user)
  ├── id, username, email, password (hashed)
  └── (related_names: chats, notifications)

Chat (chats_chat)
  ├── id, created_at
  └── participants (M2M User)

Message (chat_message_message)
  ├── id, sender (FK User), chat (FK Chat)
  ├── content, is_read, is_deleted, created_at
  └── (related_name: chat.messages)

Notification (notifications_notification)
  ├── id, user (FK User), message (FK Message)
  ├── is_read, created_at
  └── (related_names: user.notifications, message.notifications)

Token (authtoken_token)
  ├── key, user (FK User)
  └── (for authentication)
```

---

## All Systems Connected ✓

- ✓ User registration & authentication with tokens
- ✓ Chat creation with multiple participants
- ✓ Message sending with sender validation
- ✓ Auto-notifications on message.post_save signal
- ✓ Notification management (view, mark as read)
- ✓ Participant validation on all protected endpoints
- ✓ Clean JSON responses throughout
- ✓ Proper permission classes (AllowAny, IsAuthenticated)

---

**Last Updated:** March 31, 2026
