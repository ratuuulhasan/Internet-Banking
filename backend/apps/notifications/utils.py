from django.utils import timezone
from .models import Notification


def send_notification(user, title, message, channel='IN_APP'):
    """Create notification + (in real project) send via SMS/Email."""
    notif = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        channel=channel,
        status='SENT',
        sent_at=timezone.now(),
    )
    # TODO: integrate SSL Wireless / SendGrid here
    print(f"📢 Notification → {user.email}: {title} | {message}")
    return notif