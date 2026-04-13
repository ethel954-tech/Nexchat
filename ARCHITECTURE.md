# System Architecture & Connections

## Import Dependency Graph

```
config/settings.py
├── AUTH_USER_MODEL = 'userapp.User'
├── INSTALLED_APPS includes:
│   ├── rest_framework
│   ├── rest_framework.authtoken
│   ├── userapp
│   ├── chats
│   ├── chat_message
│   └── notifications
└── REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES = TokenAuthentication

config/urls.py
├── path('user/', include('userapp.urls'))
├── path('chats/', include('chats.urls'))
├── path('messages/', include('chat_message.urls'))
└── path('notifications/', include('notifications.urls'))

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

userapp/models.py
└── class User(AbstractUser)

userapp/serializers.py
├── RegisterSerializer(ModelSerializer)
│   └── validates User creation
├── LoginSerializer(Serializer)
│   └── validates username, password
└── UserSerializer(ModelSerializer)
    └── returns User(id, username, email, phone_number, status)

userapp/views.py
├── register(request)
│   └── uses RegisterSerializer
├── login(request)
│   └── uses LoginSerializer + Token.objects.get_or_create(user)
├── logout(request)
│   └── deletes request.user.auth_token
└── profile(request)
    └── uses UserSerializer

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

chats/models.py
└── class Chat(models.Model)
    ├── participants: ManyToManyField(User, related_name='chats')
    └── created_at: DateTimeField(auto_now_add=True)

chats/views.py
├── create_chat(request)
│   ├── imports: from chats.models import Chat
│   ├── imports: get_user_model()
│   ├── validates user_ids
│   └── creates Chat + adds participants
└── get_user_chats(request)
    ├── imports: Chat
    └── filters: Chat.objects.filter(participants=request.user)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

chat_message/models.py
└── class Message(models.Model)
    ├── sender: ForeignKey(settings.AUTH_USER_MODEL)
    ├── chat: ForeignKey(Chat, related_name='messages')
    ├── content: TextField()
    ├── is_read: BooleanField(default=False)
    ├── is_deleted: BooleanField(default=False)
    └── created_at: DateTimeField(auto_now_add=True)

chat_message/views.py
├── send_message(request)
│   ├── imports: from chats.models import Chat
│   ├── imports: from chat_message.models import Message
│   ├── validates Chat exists
│   ├── validates request.user in participants
│   └── creates Message
│       ├── sender = request.user
│       ├── chat = Chat
│       └── [TRIGGERS signals.post_save]
├── get_chat_messages(request, chat_id)
│   ├── validates chat participant
│   └── returns Message.objects.filter(chat=chat, is_deleted=False)
└── mark_messages_as_read(request, chat_id)
    ├── validates chat participant
    └── updates Message.objects.filter(chat=chat).update(is_read=True)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

notifications/models.py
└── class Notification(models.Model)
    ├── user: ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications')
    ├── message: ForeignKey(Message, from chat_message.models)
    ├── is_read: BooleanField(default=False)
    └── created_at: DateTimeField(auto_now_add=True)

notifications/signals.py
├── @receiver(post_save, sender=Message)
├── def create_notification(sender, instance, created, **kwargs)
│   ├── imports: from chat_message.models import Message
│   ├── imports: from .models import Notification
│   ├── if created:
│   │   └── for each chat.participants except sender:
│   │       └── Notification.objects.create(
│   │           user=participant,
│   │           message=instance
│   │       )
│   └── [FIRES ON: message.save()]
│
└── [REGISTERED IN: notifications/apps.py]

notifications/apps.py
├── class NotificationsConfig(AppConfig)
│   └── def ready(self):
│       └── import notifications.signals
│           └── [ENSURES SIGNAL RECEIVER IS REGISTERED]

notifications/views.py
├── get_notifications(request)
│   ├── imports: from .models import Notification
│   ├── filters: Notification.objects.filter(user=request.user)
│   └── returns: [notification details with message info]
├── mark_notification_as_read(request, notification_id)
│   ├── validates notification ownership
│   └── updates: notification.is_read = True
└── mark_all_notifications_as_read(request)
    ├── updates: Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    └── returns: count of updated

```

---

## Signal Flow Diagram

### When Message is Created:

```
User A calls: POST /messages/send/
                    │
                    ↓
         chat_message.views.send_message()
                    │
                    ├── Validates Chat exists
                    ├── Validates User is participant
                    │
                    ├── Message.objects.create(
                    │   sender=User A,
                    │   chat=Chat 1,
                    │   content="Hello"
                    │)
                    │
                    ↓ [TRIGGERS Django Signal]
                    │
         @receiver(post_save, sender=Message)
         create_notification()
                    │
                    ├── Gets Chat.participants except sender
                    │   └── [User B, User C]
                    │
                    ├── Notification.objects.create(
                    │   user=User B,
                    │   message=instance
                    │)
                    │
                    └── Notification.objects.create(
                        user=User C,
                        message=instance
                    )
```

---

## Request-Response Data Flow

### Scenario: User A sends message to Chat with Users B, C

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER A SENDS MESSAGE                                     │
├─────────────────────────────────────────────────────────────┤
│ POST /messages/send/                                        │
│ Headers: Authorization: Token <token_A>                    │
│ Body: {"chat_id": 1, "content": "Hello!"}                  │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "message_id": 1,                                          │
│   "sender_id": 1,                                           │
│   "chat_id": 1,                                             │
│   "content": "Hello!",                                      │
│   "created_at": "2026-03-31T10:35:00Z"                     │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 2. SIGNAL FIRES (automatic, no request)                     │
├─────────────────────────────────────────────────────────────┤
│ notifications.signals.create_notification()                │
│                                                             │
│ Creates 2 Notifications:                                    │
│ - Notification(user=User B, message=Message 1)             │
│ - Notification(user=User C, message=Message 1)             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 3. USER B GETS NOTIFICATIONS                                │
├─────────────────────────────────────────────────────────────┤
│ GET /notifications/                                         │
│ Headers: Authorization: Token <token_B>                    │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "notifications": [                                        │
│     {                                                       │
│       "id": 1,                                              │
│       "message_id": 1,                                      │
│       "chat_id": 1,                                         │
│       "sender_id": 1,                                       │
│       "content": "Hello!",                                  │
│       "is_read": false,                                     │
│       "created_at": "2026-03-31T10:35:00Z"                 │
│     }                                                       │
│   ]                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 4. USER B READS MESSAGES IN CHAT                            │
├─────────────────────────────────────────────────────────────┤
│ GET /messages/1/                                            │
│ Headers: Authorization: Token <token_B>                    │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "messages": [                                             │
│     {                                                       │
│       "message_id": 1,                                      │
│       "sender_id": 1,                                       │
│       "content": "Hello!",                                  │
│       "created_at": "2026-03-31T10:35:00Z",                │
│       "is_read": false                                      │
│     }                                                       │
│   ]                                                         │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 5. USER B MARKS MESSAGES AS READ                            │
├─────────────────────────────────────────────────────────────┤
│ POST /messages/read/1/                                      │
│ Headers: Authorization: Token <token_B>                    │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "message": "1 messages marked as read"                    │
│ }                                                           │
│                                                             │
│ Database Update:                                            │
│ Message(id=1).is_read = True                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 6. USER B MARKS NOTIFICATION AS READ                        │
├─────────────────────────────────────────────────────────────┤
│ POST /notifications/read/1/                                 │
│ Headers: Authorization: Token <token_B>                    │
│                                                             │
│ Response:                                                   │
│ {                                                           │
│   "message": "Notification marked as read"                  │
│ }                                                           │
│                                                             │
│ Database Update:                                            │
│ Notification(id=1).is_read = True                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Database State After Complete Flow

```
users:
┌────┬──────────┬──────┬──────────┐
│ id │ username │ email│ password │
├────┼──────────┼──────┼──────────┤
│ 1  │ user_a   │ ...  │ hashed   │
│ 2  │ user_b   │ ...  │ hashed   │
│ 3  │ user_c   │ ...  │ hashed   │
└────┴──────────┴──────┴──────────┘

chats:
┌────┬────────────────────┐
│ id │ created_at         │
├────┼────────────────────┤
│ 1  │ 2026-03-31 10:30   │
└────┴────────────────────┘

chat_participants (M2M):
┌────────┬─────────┐
│ chat_id│ user_id │
├────────┼─────────┤
│ 1      │ 1       │
│ 1      │ 2       │
│ 1      │ 3       │
└────────┴─────────┘

messages:
┌────┬──────────────┬─────────┬──────────────┬──────┬────────────────────┐
│ id │ sender_id    │ chat_id │ content      │ read │ created_at         │
├────┼──────────────┼─────────┼──────────────┼──────┼────────────────────┤
│ 1  │ 1            │ 1       │ Hello!       │ True │ 2026-03-31 10:35   │
└────┴──────────────┴─────────┴──────────────┴──────┴────────────────────┘

notifications:
┌────┬─────────┬────────────┬──────┬────────────────────┐
│ id │ user_id │ message_id │ read │ created_at         │
├────┼─────────┼────────────┼──────┼────────────────────┤
│ 1  │ 2       │ 1          │ True │ 2026-03-31 10:35   │
│ 2  │ 3       │ 1          │ False│ 2026-03-31 10:35   │
└────┴─────────┴────────────┴──────┴────────────────────┘

tokens:
┌──────────────────┬─────────┐
│ key              │ user_id │
├──────────────────┼─────────┤
│ token_a_hash     │ 1       │
│ token_b_hash     │ 2       │
│ token_c_hash     │ 3       │
└──────────────────┴─────────┘
```

---

## Validation & Permission Checks

### For each endpoint:

**Register (POST /user/auth/register/)**
```
✓ No auth required (AllowAny)
✓ Validate: username unique
✓ Validate: email valid format
✓ Validate: password strong
✓ Validate: password == password2
✓ Hash password before saving
```

**Login (POST /user/auth/login/)**
```
✓ No auth required (AllowAny)
✓ Validate: username exists
✓ Validate: password correct (authenticate)
✓ Create/Get token
```

**Create Chat (POST /chats/create/)**
```
✓ IsAuthenticated required
✓ Validate: user_ids exist in database
✓ Validate: all users exist
✓ Add authenticated user to participants
```

**Send Message (POST /messages/send/)**
```
✓ IsAuthenticated required
✓ Validate: chat_id exists
✓ Validate: request.user in chat.participants
✓ Create message with sender=request.user
✓ [SIGNAL] Auto-create notifications
```

**Get Messages (GET /messages/<chat_id>/)**
```
✓ IsAuthenticated required
✓ Validate: chat_id exists
✓ Validate: request.user in chat.participants
✓ Return messages (filtered is_deleted=False)
```

**Get Notifications (GET /notifications/)**
```
✓ IsAuthenticated required
✓ Filter: only request.user's notifications
✓ Return with message details
```

---

## All Systems Connected ✓

- ✓ **Auth** → Token stored in authtoken_token
- ✓ **Chats** → Participants linked via M2M
- ✓ **Messages** → Linked to Chat & User (sender)
- ✓ **Notifications** → Auto-created via signal on Message.post_save
- ✓ **Permissions** → TokenAuthentication + IsAuthenticated checks
- ✓ **Validation** → Participant checks on all protected endpoints

---

**Architecture verified and connected!** ✓
