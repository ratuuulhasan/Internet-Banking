from .models import AuditLog


def log_action(user, action, entity_type='', entity_id=None, metadata=None, request=None):
    ip = None
    ua = ''
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT', '')[:255]
    AuditLog.objects.create(
        user=user if user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        new_value=metadata or {},
        ip_address=ip,
        user_agent=ua,
    )