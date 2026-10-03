from django.contrib import admin
from .models import Bill


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['bill_id', 'user', 'biller_name', 'amount', 'status', 'due_date']
    list_filter = ['status']
    search_fields = ['user__email', 'biller_name', 'bill_number']