from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
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
