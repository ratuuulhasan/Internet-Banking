from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['user_id', 'email', 'full_name', 'phone', 'role', 'status', 'created_at']
    list_filter = ['role', 'status']
    search_fields = ['email', 'full_name', 'phone']
    ordering = ['-created_at']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('full_name', 'phone')}),
        ('Permissions', {'fields': ('role', 'status', 'is_staff', 'is_superuser', 'two_factor_enabled')}),
    )