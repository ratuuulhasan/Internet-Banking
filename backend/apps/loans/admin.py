from django.contrib import admin
from .models import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['loan_id', 'user', 'loan_type', 'principal_amount',
                    'interest_rate', 'status', 'applied_at']
    list_filter = ['status', 'loan_type']
    search_fields = ['user__email']