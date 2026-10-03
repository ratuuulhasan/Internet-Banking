from django.contrib import admin
from .models import KYC


@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = ['kyc_id', 'user', 'nid_number', 'status', 'verified_by', 'created_at']
    list_filter = ['status']
    search_fields = ['user__email', 'nid_number']
    readonly_fields = ['created_at', 'updated_at']