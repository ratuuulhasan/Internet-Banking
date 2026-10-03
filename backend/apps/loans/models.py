from django.db import models
from django.conf import settings


class Loan(models.Model):
    STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
    ]

    loan_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='loans')
    account = models.ForeignKey('accounts.Account', on_delete=models.RESTRICT)
    loan_type = models.CharField(max_length=50)
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tenure_months = models.IntegerField()
    monthly_emi = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    purpose = models.TextField(blank=True)
    ai_credit_score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='approved_loans')
    approved_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loans'
        ordering = ['-applied_at']

    def __str__(self):
        return f"Loan#{self.loan_id} - {self.loan_type} - ৳{self.principal_amount}"