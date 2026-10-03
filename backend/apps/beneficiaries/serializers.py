from rest_framework import serializers
from .models import Beneficiary


class BeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiary
        fields = ['beneficiary_id', 'name', 'account_number', 'bank_name',
                  'branch_name', 'routing_number', 'nickname', 'status', 'created_at']
        read_only_fields = ['beneficiary_id', 'created_at']