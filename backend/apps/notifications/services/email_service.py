"""
Email service — Gmail SMTP + SendGrid fallback.
"""
import logging
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_html_email(to_email, subject, html_content, text_content=None,
                    from_email=None, reply_to=None):
    """
    Send HTML email with plain text fallback.
    
    Args:
        to_email (str or list): Recipient email(s)
        subject (str): Email subject
        html_content (str): HTML body
        text_content (str, optional): Plain text fallback
        from_email (str, optional): Sender address
        reply_to (list, optional): Reply-to addresses
    
    Returns:
        dict: {'success': bool, 'error': str}
    """
    if isinstance(to_email, str):
        to_email = [to_email]

    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    text_content = text_content or strip_tags(html_content)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_email,
            reply_to=reply_to,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        logger.info(f"✅ Email sent to {to_email}: {subject}")
        return {'success': True, 'error': None}

    except Exception as e:
        logger.error(f"❌ Email failed to {to_email}: {e}")
        return {'success': False, 'error': str(e)}


def send_simple_email(to_email, subject, message):
    """Send plain text email."""
    try:
        send_mail(
            subject, message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email] if isinstance(to_email, str) else to_email,
            fail_silently=False,
        )
        logger.info(f"✅ Simple email sent to {to_email}")
        return {'success': True}
    except Exception as e:
        logger.error(f"❌ Simple email failed: {e}")
        return {'success': False, 'error': str(e)}