from rest_framework import serializers
from .models import Card


class CardSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    masked_number = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = ['card_id', 'account', 'account_number', 'masked_number',
                  'card_type', 'expiry_date', 'status', 'daily_limit', 'created_at']
        read_only_fields = ['card_id', 'card_number', 'created_at']

    def get_masked_number(self, obj):
        return f"**** **** **** {obj.card_number[-4:]}"


class CardLimitSerializer(serializers.Serializer):
    daily_limit = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0)