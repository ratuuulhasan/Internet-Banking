from django.db import models
from django.conf import settings


class Beneficiary(models.Model):
    beneficiary_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='beneficiaries')
    name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=30)
    bank_name = models.CharField(max_length=100, blank=True)
    branch_name = models.CharField(max_length=100, blank=True)
    routing_number = models.CharField(max_length=20, blank=True)
    nickname = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'beneficiaries'
        unique_together = ('user', 'account_number')

    def __str__(self):
        return f"{self.name} - {self.account_number}"