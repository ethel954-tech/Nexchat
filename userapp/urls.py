from django.urls import path
from .views import register, login, logout, profile, register_page, login_page, profile_page

app_name = 'userapp'

urlpatterns = [
    # API endpoints
    path('auth/register/', register, name='register'),
    path('auth/login/', login, name='login'),
    path('auth/logout/', logout, name='logout'),
    path('auth/profile/', profile, name='profile'),
    # Template pages
    path('register-page/', register_page, name='register_page'),
    path('login-page/', login_page, name='login_page'),
    path('profile-page/', profile_page, name='profile_page'),
]
