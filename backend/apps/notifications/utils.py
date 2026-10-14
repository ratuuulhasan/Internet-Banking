"""
Notification service — unified interface for SMS + Email + In-App.
"""
import logging
from django.utils import timezone
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)


# ============================================================
# CORE SENDER
# ============================================================

def send_notification(user, title, message, channel='IN_APP',
                     email_html=None, sms_text=None):
    """
    Send notification via multiple channels.

    Args:
        user: User instance
        title: str
        message: str (for in-app)
        channel: IN_APP|EMAIL|SMS|ALL
        email_html: str (optional)
        sms_text: str (optional)

    Returns:
        dict: per-channel result
    """
    if channel == 'ALL':
        channels = ['IN_APP', 'EMAIL', 'SMS']
    else:
        channels = [channel]

    results = {}

    # ---- In-App ----
    if 'IN_APP' in channels:
        try:
            notif = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                channel='IN_APP',
                status='SENT',
                sent_at=timezone.now(),
            )
            results['in_app'] = {'success': True, 'id': notif.notification_id}
        except Exception as e:
            logger.error(f"In-app notification failed: {e}")
            results['in_app'] = {'success': False, 'error': str(e)}

    # ---- Email ----
    if 'EMAIL' in channels and user.email:
        try:
            from .services.email_service import send_html_email
            html = email_html or f"<h3>{title}</h3><p>{message}</p>"
            results['email'] = send_html_email(user.email, title, html)
        except Exception as e:
            logger.error(f"Email notification error: {e}")
            results['email'] = {'success': False, 'error': str(e)}

    # ---- SMS ----
    if 'SMS' in channels and user.phone:
        try:
            from .services.sms_service import send_sms
            text = sms_text or f"{title}: {message}"
            results['sms'] = send_sms(user.phone, text)
        except Exception as e:
            logger.error(f"SMS notification error: {e}")
            results['sms'] = {'success': False, 'error': str(e)}

    return results


# ============================================================
# HIGH-LEVEL HELPERS
# ============================================================

def notify_welcome(user):
    """Send welcome email after registration."""
    if not settings.NOTIFICATION_SETTINGS.get('SEND_WELCOME_EMAIL'):
        return

    try:
        from .services.email_service import send_html_email
        from .services.templates import welcome_email_template

        html = welcome_email_template(user.full_name, user.email)
        send_html_email(
            user.email,
            '🏦 Welcome to Internet Banking',
            html,
        )
    except Exception as e:
        logger.error(f"Welcome email failed: {e}")


def notify_transaction(user, txn_data):
    """Send transaction notification (email + SMS)."""
    if settings.NOTIFICATION_SETTINGS.get('SEND_TRANSACTION_EMAIL'):
        try:
            from .services.email_service import send_html_email
            from .services.templates import transaction_email_template

            html = transaction_email_template(user.full_name, txn_data)
            send_html_email(
                user.email,
                f"💸 Transaction {txn_data.get('status')} — ৳{txn_data.get('amount')}",
                html,
            )
        except Exception as e:
            logger.error(f"Transaction email failed: {e}")

    if settings.NOTIFICATION_SETTINGS.get('SEND_TRANSACTION_SMS'):
        try:
            from .services.sms_service import send_sms
            from .services.templates import transaction_sms_template

            sms = transaction_sms_template(txn_data)
            send_sms(user.phone, sms)
        except Exception as e:
            logger.error(f"Transaction SMS failed: {e}")


def notify_kyc_status(user, status, remarks=''):
    """Send KYC approval/rejection notification."""
    if settings.NOTIFICATION_SETTINGS.get('SEND_KYC_STATUS_EMAIL'):
        try:
            from .services.email_service import send_html_email
            from .services.templates import kyc_status_email_template

            html = kyc_status_email_template(user.full_name, status, remarks)
            subject = f"KYC {status} — Internet Banking"
            send_html_email(user.email, subject, html)
        except Exception as e:
            logger.error(f"KYC email failed: {e}")

    if settings.NOTIFICATION_SETTINGS.get('SEND_KYC_STATUS_SMS'):
        try:
            from .services.sms_service import send_sms
            msg = (
                f"IB Alert: Your KYC is {status}. "
                + (f"Reason: {remarks[:80]}" if status == 'REJECTED' and remarks else "")
            )
            send_sms(user.phone, msg)
        except Exception as e:
            logger.error(f"KYC SMS failed: {e}")


def notify_loan_status(user, loan_data, status):
    """Send loan status notification."""
    if not settings.NOTIFICATION_SETTINGS.get('SEND_LOAN_STATUS_EMAIL'):
        return

    try:
        from .services.email_service import send_html_email

        html = f"""
        <h2>Loan Application {status}</h2>
        <p>প্রিয় {user.full_name},</p>
        <p>আপনার loan application ({loan_data.get('loan_type')}) 
        এর status: <strong>{status}</strong></p>
        <p>Amount: ৳ {loan_data.get('principal_amount')}</p>
        <p>Monthly EMI: ৳ {loan_data.get('monthly_emi', 'N/A')}</p>
        """
        send_html_email(
            user.email,
            f"💰 Loan Application {status}",
            html,
        )
    except Exception as e:
        logger.error(f"Loan email failed: {e}")


def notify_complaint_update(user, complaint_data):
    """Send complaint/ticket update notification."""
    if not settings.NOTIFICATION_SETTINGS.get('SEND_COMPLAINT_UPDATES'):
        return

    try:
        from .services.email_service import send_html_email

        html = f"""
        <h2>Ticket Update</h2>
        <p>প্রিয় {user.full_name},</p>
        <p>Ticket #{complaint_data.get('ticket_id')} — {complaint_data.get('subject')}</p>
        <p>Status: <strong>{complaint_data.get('status')}</strong></p>
        {f'<p>Note: {complaint_data.get("resolution_note")}</p>' if complaint_data.get('resolution_note') else ''}
        """
        send_html_email(
            user.email,
            f"🎫 Ticket #{complaint_data.get('ticket_id')} Updated",
            html,
        )
    except Exception as e:
        logger.error(f"Complaint email failed: {e}")