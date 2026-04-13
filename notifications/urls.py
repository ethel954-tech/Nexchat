from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.get_notifications, name='get_notifications'),
    path('read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('read-all/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
]
