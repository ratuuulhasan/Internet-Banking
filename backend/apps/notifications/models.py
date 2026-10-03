from django.db import models
from django.conf import settings


class Notification(models.Model):
    CHANNEL = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push'),
        ('IN_APP', 'In App'),
    ]
    STATUS = [('PENDING', 'Pending'), ('SENT', 'Sent'), ('FAILED', 'Failed')]

    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    channel = models.CharField(max_length=10, choices=CHANNEL, default='IN_APP')
    status = models.CharField(max_length=10, choices=STATUS, default='PENDING')
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.channel}] {self.title} → {self.user.email}"