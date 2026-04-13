from django.urls import path
from . import views

app_name = 'chats_api'

urlpatterns = [
    path('create/', views.create_chat, name='create_chat'),
    path('', views.get_user_chats, name='get_user_chats'),
    path('saved/', views.saved_messages_api, name='saved_messages_api'),
    path('saved/<int:saved_id>/', views.delete_saved_message, name='delete_saved_message'),
    path('channels/', views.channels_api, name='channels_api'),
    path('channels/<int:channel_id>/', views.channel_detail_api, name='channel_detail_api'),
]
