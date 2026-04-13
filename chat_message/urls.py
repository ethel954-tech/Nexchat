from django.urls import path
from . import views

app_name = 'chat_message'

urlpatterns = [
    path('send/', views.send_message, name='send_message'),
    path('<int:chat_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('read/<int:chat_id>/', views.mark_messages_as_read, name='mark_messages_as_read'),
    path('upload/', views.upload_message_media, name='upload_message_media'),
]
