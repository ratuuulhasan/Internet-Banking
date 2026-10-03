from django.db import models
from django.conf import settings


class Bill(models.Model):
    STATUS = [
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]

    bill_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='bills')
    biller_name = models.CharField(max_length=100)
    biller_code = models.CharField(max_length=50, blank=True)
    bill_number = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='UNPAID')
    paid_transaction = models.ForeignKey('transactions.Transaction',
                                         on_delete=models.SET_NULL,
                                         null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bills'
        ordering = ['-created_at']

    def __str__(self):
        return f"Bill#{self.bill_id} - {self.biller_name} - ৳{self.amount}"