from rest_framework import serializers
from .models import Bill


class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ['bill_id', 'biller_name', 'biller_code', 'bill_number',
                  'amount', 'due_date', 'status', 'paid_transaction', 'created_at']
        read_only_fields = ['bill_id', 'status', 'paid_transaction', 'created_at']


class BillPaymentSerializer(serializers.Serializer):
    bill_id = serializers.IntegerField()
    from_account_id = serializers.IntegerField()
    otp_code = serializers.CharField(min_length=6, max_length=6)