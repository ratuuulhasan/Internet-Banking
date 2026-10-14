"""
Celery tasks for async notification sending.
Prevents blocking the request cycle for email/SMS APIs.
"""
from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email_task(self, user_id):
    """Async welcome email."""
    try:
        user = User.objects.get(user_id=user_id)
        from .utils import notify_welcome
        notify_welcome(user)
        return {'status': 'success', 'user_id': user_id}
    except User.DoesNotExist:
        return {'status': 'user_not_found', 'user_id': user_id}
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_transaction_notification_task(self, user_id, txn_data):
    """Async transaction notification."""
    try:
        user = User.objects.get(user_id=user_id)
        from .utils import notify_transaction
        notify_transaction(user, txn_data)
        return {'status': 'success'}
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_kyc_status_task(self, user_id, status, remarks=''):
    """Async KYC status notification."""
    try:
        user = User.objects.get(user_id=user_id)
        from .utils import notify_kyc_status
        notify_kyc_status(user, status, remarks)
        return {'status': 'success'}
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_loan_status_task(self, user_id, loan_data, status):
    """Async loan status notification."""
    try:
        user = User.objects.get(user_id=user_id)
        from .utils import notify_loan_status
        notify_loan_status(user, loan_data, status)
        return {'status': 'success'}
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_complaint_update_task(self, user_id, complaint_data):
    """Async complaint update notification."""
    try:
        user = User.objects.get(user_id=user_id)
        from .utils import notify_complaint_update
        notify_complaint_update(user, complaint_data)
        return {'status': 'success'}
    except Exception as e:
        raise self.retry(exc=e)