"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from chats import views as chat_views

urlpatterns = [
    path('', RedirectView.as_view(url='/chats/', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    path('saved/', chat_views.saved_messages_view, name='saved_messages'),
    path('contacts/', chat_views.contacts_view, name='contacts'),
    path('groups/create/', chat_views.create_group_view, name='create_group'),
    path('channels/create/', chat_views.create_channel_view, name='create_channel'),
    path('status/', chat_views.status_view, name='status'),
    path('status/privacy/', chat_views.status_privacy_view, name='status_privacy'),
    path('profile/<int:user_id>/', chat_views.contact_profile_view, name='profile_detail'),
    path('profile/', chat_views.profile, name='profile'),
    path('settings/', chat_views.settings_view, name='settings'),
    path('user/', include('userapp.urls')),
    path('api/user/', include('userapp.api_urls')),
    path('messages/', include(('chat_message.urls', 'chat_message'), namespace='chat_message')),
    path('api/messages/', include(('chat_message.urls', 'chat_message_api'), namespace='chat_message_api')),
    path('notifications/', include('notifications.urls')),
    path('api/notifications/', include(('notifications.urls', 'notifications_api'), namespace='notifications_api')),
    path('chats/', include('chats.urls')),  # frontend
    path('api/chats/', include('chats.api_urls')),  # API
    path('api/status/', include('statusfeed.api_urls')),
] + (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else [])
