from django.db import models
from django.conf import settings


class Complaint(models.Model):
    STATUS = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    PRIORITY = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')]

    ticket_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='complaints')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='OPEN')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='MEDIUM')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='assigned_tickets')
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'complaints_tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket#{self.ticket_id} - {self.subject} [{self.status}]"