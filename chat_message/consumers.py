import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from chat_message.models import Message
from chats.models import Chat

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            content = data.get('message', '')
            
            # Save message to database
            message = await self.save_message(content)
            
            if message:
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'content': message.content,
                            'sender_id': message.sender.id,
                            'sender_username': message.sender.username,
                            'created_at': message.created_at.isoformat(),
                            'media_url': message.media.url if message.media else None,
                        }
                    }
                )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

    @database_sync_to_async
    def save_message(self, content):
        try:
            chat = Chat.objects.get(id=self.chat_id)
            
            # Check if user is participant
            if not chat.participants.filter(id=self.user.id).exists():
                return None
            
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                content=content
            )
            return message
        except Chat.DoesNotExist:
            return None
