from django.db import models
from django.conf import settings


class KYC(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing (OCR)'),
        ('OCR_DONE', 'OCR Complete'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    kyc_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='kyc'
    )

    # ---- User Submitted Data ----
    nid_number = models.CharField(max_length=50, unique=True)
    dob = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    document_type = models.CharField(max_length=50, default='NID')

    # ---- Uploaded Files ----
    document_front = models.ImageField(upload_to='kyc/', null=True, blank=True)
    document_back = models.ImageField(upload_to='kyc/', null=True, blank=True)
    selfie = models.ImageField(upload_to='kyc/', null=True, blank=True)

    # ---- OCR Extracted Data (AI Service) ----
    ocr_extracted = models.JSONField(
        null=True, blank=True,
        help_text="Full OCR response from AI service"
    )
    ocr_name_bangla = models.CharField(max_length=150, blank=True)
    ocr_name_english = models.CharField(max_length=150, blank=True)
    ocr_father_name = models.CharField(max_length=150, blank=True)
    ocr_mother_name = models.CharField(max_length=150, blank=True)
    ocr_dob = models.CharField(max_length=50, blank=True)
    ocr_blood_group = models.CharField(max_length=10, blank=True)
    ocr_address = models.TextField(blank=True)
    ocr_issue_date = models.CharField(max_length=50, blank=True)
    ocr_confidence = models.FloatField(null=True, blank=True)
    ocr_fields_extracted = models.IntegerField(default=0)

    # ---- Verification Scores ----
    tamper_score = models.FloatField(null=True, blank=True)
    tamper_risk_level = models.CharField(max_length=20, blank=True)
    is_tampered = models.BooleanField(default=False)

    face_match_similarity = models.FloatField(null=True, blank=True)
    face_matched = models.BooleanField(null=True, blank=True)

    # ---- Verification Decision ----
    verification_score = models.FloatField(null=True, blank=True)
    auto_approve = models.BooleanField(default=False)
    needs_manual_review = models.BooleanField(default=True)

    # ---- Status & Admin ----
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_kycs'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    ocr_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kyc'
        ordering = ['-created_at']

    def __str__(self):
        return f"KYC #{self.kyc_id} - {self.user.email} [{self.status}]"

    @property
    def has_ocr_data(self):
        return self.ocr_extracted is not None

    @property
    def ocr_summary(self):
        """Quick summary for admin list view."""
        if not self.has_ocr_data:
            return {'status': 'no_ocr'}
        return {
            'name': self.ocr_name_english or self.ocr_name_bangla or '-',
            'confidence': self.ocr_confidence,
            'fields': self.ocr_fields_extracted,
            'tamper_risk': self.tamper_risk_level,
            'face_match': self.face_matched,
            'auto_approve': self.auto_approve,
        }