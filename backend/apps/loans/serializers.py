from rest_framework import serializers
from .models import Loan


class LoanSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Loan
        fields = ['loan_id', 'user', 'user_email', 'account', 'loan_type',
                  'principal_amount', 'interest_rate', 'tenure_months',
                  'monthly_emi', 'purpose', 'ai_credit_score', 'status',
                  'approved_by', 'approved_at', 'applied_at']
        read_only_fields = ['loan_id', 'user', 'monthly_emi', 'ai_credit_score',
                            'status', 'approved_by', 'approved_at', 'applied_at']


class LoanDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'])