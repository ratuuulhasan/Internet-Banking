from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_id', 'user', 'title', 'channel', 'status', 'is_read']
    list_filter = ['channel', 'status', 'is_read']