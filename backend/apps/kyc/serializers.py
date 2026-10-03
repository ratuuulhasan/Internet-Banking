from rest_framework import serializers
from .models import KYC


class KYCSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = KYC
        fields = [
            'kyc_id', 'user', 'user_email', 'user_name',
            'nid_number', 'dob', 'address', 'document_type',
            'document_front', 'document_back', 'selfie',
            'status', 'verified_by', 'verified_at', 'remarks',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['kyc_id', 'user', 'status', 'verified_by',
                            'verified_at', 'created_at', 'updated_at']


class KYCApprovalSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'])
    remarks = serializers.CharField(required=False, allow_blank=True)