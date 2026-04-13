from django.urls import path
from . import views

app_name = 'chats'

urlpatterns = [
    # Frontend template views
    path('', views.chat_list_page, name='chat_list'),
    path('<int:chat_id>/', views.chat_room_page, name='chat_room'),
]
