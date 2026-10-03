from django.db import models
from django.conf import settings


class KYC(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    kyc_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='kyc'
    )
    nid_number = models.CharField(max_length=50, unique=True)
    dob = models.DateField()
    address = models.TextField()
    document_type = models.CharField(max_length=50, default='NID')
    document_front = models.ImageField(upload_to='kyc/', null=True, blank=True)
    document_back = models.ImageField(upload_to='kyc/', null=True, blank=True)
    selfie = models.ImageField(upload_to='kyc/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_kycs'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kyc'
        ordering = ['-created_at']

    def __str__(self):
        return f"KYC #{self.kyc_id} - {self.user.email} [{self.status}]"