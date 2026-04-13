from django.urls import path
from . import views

app_name = 'userapp_api'

urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.profile, name='profile'),
    path('contacts/', views.contacts, name='contacts'),
    path('contacts/refresh/', views.refresh_contacts, name='contacts_refresh'),
    path('status/privacy/', views.status_privacy_settings, name='status_privacy'),
    path('people/<int:user_id>/', views.user_detail, name='user_detail'),
]
