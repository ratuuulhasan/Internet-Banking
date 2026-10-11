from rest_framework import serializers
from .models import KYC


class KYCSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    ocr_summary = serializers.ReadOnlyField()

    class Meta:
        model = KYC
        fields = [
            'kyc_id', 'user', 'user_email', 'user_name',
            # Submitted
            'nid_number', 'dob', 'address', 'document_type',
            'document_front', 'document_back', 'selfie',
            # OCR Extracted
            'ocr_extracted', 'ocr_name_bangla', 'ocr_name_english',
            'ocr_father_name', 'ocr_mother_name', 'ocr_dob',
            'ocr_blood_group', 'ocr_address', 'ocr_issue_date',
            'ocr_confidence', 'ocr_fields_extracted', 'ocr_summary',
            # Tamper
            'tamper_score', 'tamper_risk_level', 'is_tampered',
            # Face
            'face_match_similarity', 'face_matched',
            # Decision
            'verification_score', 'auto_approve', 'needs_manual_review',
            # Admin
            'status', 'verified_by', 'verified_at', 'remarks', 'ocr_error',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'kyc_id', 'user',
            'ocr_extracted', 'ocr_name_bangla', 'ocr_name_english',
            'ocr_father_name', 'ocr_mother_name', 'ocr_dob',
            'ocr_blood_group', 'ocr_address', 'ocr_issue_date',
            'ocr_confidence', 'ocr_fields_extracted',
            'tamper_score', 'tamper_risk_level', 'is_tampered',
            'face_match_similarity', 'face_matched',
            'verification_score', 'auto_approve', 'needs_manual_review',
            'status', 'verified_by', 'verified_at', 'created_at', 'updated_at',
            'ocr_error',
        ]


class KYCApprovalSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'])
    remarks = serializers.CharField(required=False, allow_blank=True)


class KYCSubmitSerializer(serializers.Serializer):
    """Minimal serializer for KYC submission."""
    nid_number = serializers.CharField(max_length=50)
    dob = serializers.DateField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.CharField(default='NID', required=False)