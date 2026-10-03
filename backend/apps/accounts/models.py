from django.db import models
from django.conf import settings
import random


class Account(models.Model):
    ACCOUNT_TYPE = [
        ('SAVINGS', 'Savings'),
        ('CURRENT', 'Current'),
        ('FIXED_DEPOSIT', 'Fixed Deposit'),
        ('LOAN', 'Loan'),
    ]
    STATUS = [
        ('ACTIVE', 'Active'),
        ('DORMANT', 'Dormant'),
        ('CLOSED', 'Closed'),
        ('FROZEN', 'Frozen'),
    ]

    account_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=30, unique=True, db_index=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE, default='SAVINGS')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='BDT')
    status = models.CharField(max_length=20, choices=STATUS, default='ACTIVE')
    branch_code = models.CharField(max_length=20, blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts'
        ordering = ['-opened_at']

    def __str__(self):
        return f"{self.account_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = self.generate_account_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_account_number():
        while True:
            num = '10' + ''.join([str(random.randint(0, 9)) for _ in range(10)])
            if not Account.objects.filter(account_number=num).exists():
                return num