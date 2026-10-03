from django.contrib import admin
from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['card_id', 'card_number', 'card_type', 'status', 'daily_limit']
    list_filter = ['card_type', 'status']
    search_fields = ['card_number']