from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from chats.models import Chat
from chat_message.models import Message

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample users, chats, and seeded messages for quick demos.'

    def handle(self, *args, **options):
        with transaction.atomic():
            users = self._create_users()
            chats = self._create_chats(users)
            self._create_messages(users, chats)

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write(self.style.WARNING('Login with john_doe/password123 or any other sample account.'))

    def _create_users(self):
        users_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 'password': 'password123'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'password': 'password123'},
            {'username': 'bob_wilson', 'email': 'bob@example.com', 'password': 'password123'},
            {'username': 'alice_johnson', 'email': 'alice@example.com', 'password': 'password123'},
        ]

        users = []
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={'email': data['email']}
            )
            user.email = data['email']
            user.set_password(data['password'])
            user.save()
            users.append(user)
            verb = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{verb} user {user.username}'))

        return users

    def _create_chats(self, users):
        chats_config = [
            {'participants': [users[0], users[1]]},
            {'participants': [users[0], users[1], users[2]]},
            {'participants': [users[2], users[3]]},
            {'participants': [users[0], users[2], users[3]]},
        ]

        chats = []
        for config in chats_config:
            chat = Chat.objects.create()
            chat.participants.set(config['participants'])
            chats.append(chat)
            self.stdout.write(self.style.SUCCESS(f'Created chat {chat.id} with {chat.participants.count()} participants'))

        return chats

    def _create_messages(self, users, chats):
        messages_data = [
            {"content": "Hey Jane! How are you?", "sender": users[0], "chat": chats[0]},
            {"content": "Doing great John! What's up?", "sender": users[1], "chat": chats[0]},
            {"content": "Meeting tomorrow at 2pm?", "sender": users[0], "chat": chats[0]},
            {"content": "Perfect! See you then.", "sender": users[1], "chat": chats[0]},
            {"content": "Team, status update?", "sender": users[0], "chat": chats[1]},
            {"content": "On track with deliverables.", "sender": users[2], "chat": chats[1]},
            {"content": "Bob, lunch plans?", "sender": users[3], "chat": chats[2]},
            {"content": "Cafeteria at 12?", "sender": users[2], "chat": chats[2]},
        ]

        for entry in messages_data:
            message = Message.objects.create(
                sender=entry['sender'],
                chat=entry['chat'],
                content=entry['content']
            )
            self.stdout.write(self.style.SUCCESS(f'Added message {message.id} in chat {message.chat_id}'))
