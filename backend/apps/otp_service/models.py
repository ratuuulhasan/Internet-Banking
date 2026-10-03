from django.db import models
from django.conf import settings
import hashlib


class OTPVerification(models.Model):
    PURPOSE = [
        ('LOGIN', 'Login'),
        ('TRANSFER', 'Transfer'),
        ('BILL_PAYMENT', 'Bill Payment'),
        ('PROFILE_UPDATE', 'Profile Update'),
    ]

    otp_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp_code_hash = models.CharField(max_length=255)
    purpose = models.CharField(max_length=20, choices=PURPOSE)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_verifications'