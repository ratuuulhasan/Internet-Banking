from django.db import models
from django.conf import settings
import uuid


class Transaction(models.Model):
    TYPE = [
        ('TRANSFER', 'Transfer'),
        ('BILL_PAYMENT', 'Bill Payment'),
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('LOAN_PAYMENT', 'Loan Payment'),
        ('RECHARGE', 'Mobile Recharge'),
    ]
    STATUS = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REVERSED', 'Reversed'),
        ('HELD', 'Held for Review'),
    ]

    transaction_id = models.AutoField(primary_key=True)
    reference_no = models.CharField(max_length=50, unique=True, db_index=True)
    from_account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.RESTRICT,
        related_name='outgoing_transactions'
    )
    to_account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.RESTRICT,
        related_name='incoming_transactions',
        null=True, blank=True
    )
    beneficiary = models.ForeignKey(
        'beneficiaries.Beneficiary',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    transaction_type = models.CharField(max_length=20, choices=TYPE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='BDT')
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    description = models.TextField(blank=True)
    otp_verified = models.BooleanField(default=False)

    # ============ AI FRAUD FIELDS ============
    fraud_score = models.FloatField(null=True, blank=True)
    fraud_explanation = models.JSONField(
        null=True, blank=True,
        help_text="SHAP feature contributions"
    )
    risk_level = models.CharField(
        max_length=10, blank=True,
        help_text="SAFE/LOW/MEDIUM/HIGH"
    )
    # =========================================

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['from_account', 'created_at']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.reference_no:
            self.reference_no = 'TXN' + uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference_no