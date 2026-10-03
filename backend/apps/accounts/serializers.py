from rest_framework import serializers
from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['account_id', 'account_number', 'account_type', 'balance',
                  'currency', 'status', 'branch_code', 'opened_at']
        read_only_fields = fields