from django.contrib import admin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['ticket_id', 'user', 'subject', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['subject', 'user__email']