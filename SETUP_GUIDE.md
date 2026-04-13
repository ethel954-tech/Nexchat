# Setup & Migration Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install django djangorestframework django-rest-framework-authtoken python-dotenv pillow
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

This creates all necessary tables:
- `django.contrib.auth` tables
- `django.contrib.contenttypes` tables
- `userapp.User` (custom user model)
- `chats.Chat` and chat_participants table
- `chat_message.Message` tables
- `notifications.Notification` tables
- `authtoken_token` table (for Token Authentication)

### 3. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 4. Start Development Server
```bash
python manage.py runserver
```

Server runs at: `http://localhost:8000`

---

## API Endpoint Summary

### Authentication (`/user/`)
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/user/auth/register/` | AllowAny | Register new user |
| POST | `/user/auth/login/` | AllowAny | Login & get token |
| GET | `/user/auth/profile/` | IsAuthenticated | Get user profile |
| POST | `/user/auth/logout/` | IsAuthenticated | Logout (delete token) |

### Chats (`/chats/`)
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/chats/create/` | IsAuthenticated | Create new chat |
| GET | `/chats/` | IsAuthenticated | Get user's chats |

### Messages (`/messages/`)
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/messages/send/` | IsAuthenticated | Send message |
| GET | `/messages/<chat_id>/` | IsAuthenticated | Get chat messages |
| POST | `/messages/read/<chat_id>/` | IsAuthenticated | Mark as read |

### Notifications (`/notifications/`)
| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/notifications/` | IsAuthenticated | Get notifications |
| POST | `/notifications/read/<id>/` | IsAuthenticated | Mark single as read |
| POST | `/notifications/read-all/` | IsAuthenticated | Mark all as read |

---

## Testing the API

### Using cURL or REST Client

#### Step 1: Register
```bash
curl -X POST http://localhost:8000/user/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!"
  }'
```

#### Step 2: Login
```bash
curl -X POST http://localhost:8000/user/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
    "message": "Login successful",
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 1,
    "username": "john_doe"
}
```

#### Step 3: Create Chat
```bash
curl -X POST http://localhost:8000/chats/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -d '{
    "user_ids": [2, 3]
  }'
```

#### Step 4: Send Message
```bash
curl -X POST http://localhost:8000/messages/send/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -d '{
    "chat_id": 1,
    "content": "Hello everyone!"
  }'
```

#### Step 5: Get Notifications
```bash
curl -X GET http://localhost:8000/notifications/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

---

## Troubleshooting

### Migration Issues
```bash
# If you have migration conflicts:
python manage.py showmigrations
python manage.py migrate app_name
```

### Token Not Working
- Ensure `rest_framework.authtoken` is in INSTALLED_APPS
- Verify token exists: `localhost:8000/admin/authtoken/token/`
- Check token format: `Authorization: Token <token_key>`

### Message Signal Not Triggering
- Verify `notifications.apps.NotificationsConfig` has `ready()` method
- Check that `import notifications.signals` is in `apps.py`
- Verify app order in INSTALLED_APPS

### Permission Denied
- Some endpoints require `IsAuthenticated`
- Always include auth token header for protected endpoints
- Register/login endpoints use `AllowAny` (no token needed)

---

## Production Considerations

1. **Security**
   - Set `DEBUG = False` in production
   - Use SSL/HTTPS
   - Use strong `SECRET_KEY`
   - Set proper `ALLOWED_HOSTS`

2. **Database**
   - Use PostgreSQL instead of SQLite
   - Set up proper backups
   - Use connection pooling

3. **Authentication**
   - Token expiration (optional: add package for this)
   - Two-factor authentication (optional)
   - Rate limiting on login endpoint

4. **Performance**
   - Add database indexes on frequently queried fields
   - Implement pagination for list endpoints
   - Use database query optimization

---

## File Structure Verification

Ensure all files exist:

```
✓ config/settings.py          (AUTH_USER_MODEL, REST_FRAMEWORK, INSTALLED_APPS)
✓ config/urls.py              (URL routing)
✓ config/asgi.py              (ASGI config)
✓ config/wsgi.py              (WSGI config)

✓ userapp/models.py           (User model)
✓ userapp/serializers.py      (Register, Login, User serializers)
✓ userapp/views.py            (register, login, logout, profile)
✓ userapp/urls.py             (auth endpoints)

✓ chats/models.py             (Chat model)
✓ chats/views.py              (create_chat, get_user_chats)
✓ chats/urls.py               (chat endpoints)

✓ chat_message/models.py      (Message model)
✓ chat_message/views.py       (send_message, get_messages, mark_read)
✓ chat_message/urls.py        (message endpoints)

✓ notifications/models.py     (Notification model)
✓ notifications/signals.py    (auto-create notifications)
✓ notifications/apps.py       (AppConfig with ready())
✓ notifications/views.py      (get_notifications, mark as read)
✓ notifications/urls.py       (notification endpoints)

✓ .env                         (SECRET_KEY, DEBUG settings)
✓ .gitignore                   (ignore venv, .env, etc.)
```

---

## Common Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Access Django shell
python manage.py shell

# Check migrations status
python manage.py showmigrations

# Run tests
python manage.py test

# Create fixture (backup data)
python manage.py dumpdata > backup.json

# Load fixture (restore data)
python manage.py loaddata backup.json
```

---

**System is ready for deployment!** ✓
