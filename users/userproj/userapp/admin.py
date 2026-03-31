from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': (
                'phone_number',
                'profile_picture',
                'status',
                'last_seen',
                'last_seen_privacy',
                'read_receipts',
                'blocked_users',
            )
        }),
    )
    list_display = ['username', 'email', 'phone_number', 'last_seen']

