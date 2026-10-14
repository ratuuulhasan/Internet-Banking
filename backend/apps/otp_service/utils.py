"""
OTP Service — send via SMS + Email.
"""
import random
import hashlib
import logging
from datetime import timedelta
from django.utils import timezone
from .models import OTPVerification

logger = logging.getLogger(__name__)


def generate_otp(user, purpose='TRANSFER', send_sms=True, send_email=True):
    """
    Generate OTP and send via SMS + Email.

    Returns:
        dict: {'otp_sent': bool, 'sms': result, 'email': result, 'otp': str}
    """
    # Generate code
    code = f"{random.randint(100000, 999999)}"
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    # Save to DB
    OTPVerification.objects.create(
        user=user,
        otp_code_hash=code_hash,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=5),
    )

    results = {'otp_sent': False, 'sms': None, 'email': None, 'otp': code}

    # ---- Send SMS ----
    if send_sms and user.phone:
        try:
            from apps.notifications.services.sms_service import send_sms as sms_send
            from apps.notifications.services.templates import otp_sms_template

            message = otp_sms_template(code, purpose)
            sms_result = sms_send(user.phone, message)
            results['sms'] = sms_result
            if sms_result.get('success'):
                results['otp_sent'] = True
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            results['sms'] = {'success': False, 'error': str(e)}

    # ---- Send Email ----
    if send_email and user.email:
        try:
            from apps.notifications.services.email_service import send_html_email
            from apps.notifications.services.templates import otp_email_template

            html = otp_email_template(user.full_name, code, purpose)
            email_result = send_html_email(
                user.email,
                f'🔐 Your OTP for {purpose}',
                html,
            )
            results['email'] = email_result
            if email_result.get('success'):
                results['otp_sent'] = True
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            results['email'] = {'success': False, 'error': str(e)}

    # Console fallback (dev)
    if not results['otp_sent']:
        print(f"\n⚠️ All delivery methods failed. OTP for {user.email}: {code}\n")

    return results


def verify_otp(user, code, purpose):
    """Verify OTP code."""
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    otp = OTPVerification.objects.filter(
        user=user,
        otp_code_hash=code_hash,
        purpose=purpose,
        is_used=False,
        expires_at__gt=timezone.now(),
    ).first()

    if otp:
        otp.is_used = True
        otp.save()
        return True
    return False