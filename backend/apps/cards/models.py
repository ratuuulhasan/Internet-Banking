from django.db import models


class Card(models.Model):
    CARD_TYPE = [('DEBIT', 'Debit'), ('CREDIT', 'Credit')]
    STATUS = [('ACTIVE', 'Active'), ('BLOCKED', 'Blocked'), ('EXPIRED', 'Expired')]

    card_id = models.AutoField(primary_key=True)
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE,
                                related_name='cards')
    card_number = models.CharField(max_length=20, unique=True)
    card_type = models.CharField(max_length=10, choices=CARD_TYPE)
    expiry_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS, default='ACTIVE')
    daily_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cards'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.card_type} - ****{self.card_number[-4:]}"