from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    from_account_number = serializers.CharField(source='from_account.account_number', read_only=True)
    to_account_number = serializers.CharField(source='to_account.account_number', read_only=True)

    class Meta:
        model = Transaction
        fields = ['transaction_id', 'reference_no', 'from_account', 'from_account_number',
                  'to_account', 'to_account_number', 'transaction_type', 'amount',
                  'currency', 'status', 'description', 'created_at', 'completed_at']
        read_only_fields = fields


class TransferSerializer(serializers.Serializer):
    from_account_id = serializers.IntegerField()
    to_account_number = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=1)
    description = serializers.CharField(required=False, allow_blank=True)
    otp_code = serializers.CharField(required=True, min_length=6, max_length=6)

class TransactionSerializer(serializers.ModelSerializer):
    from_account_number = serializers.CharField(
        source='from_account.account_number', read_only=True
    )
    to_account_number = serializers.CharField(
        source='to_account.account_number', read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'reference_no',
            'from_account', 'from_account_number',
            'to_account', 'to_account_number',
            'transaction_type', 'amount', 'currency',
            'status', 'description', 'created_at', 'completed_at',
            # 👇 NEW
            'fraud_score', 'risk_level', 'fraud_explanation',
        ]
        read_only_fields = fields