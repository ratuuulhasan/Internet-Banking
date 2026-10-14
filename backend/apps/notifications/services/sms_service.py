"""
SMS service — Twilio + SSL Wireless (Bangladesh) + Console fallback.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(to_phone, message):
    """
    Send SMS via configured provider.
    
    Args:
        to_phone (str): Phone number with country code (+8801XXXXXXXXX)
        message (str): SMS text (160 chars max)
    
    Returns:
        dict: {'success': bool, 'provider': str, 'error': str}
    """
    provider = getattr(settings, 'SMS_PROVIDER', 'console').lower()

    # Truncate to 160 chars
    if len(message) > 160:
        message = message[:157] + '...'

    if provider == 'twilio':
        return _send_twilio(to_phone, message)
    elif provider == 'sslwireless':
        return _send_sslwireless(to_phone, message)
    else:
        return _send_console(to_phone, message)


def _send_twilio(to_phone, message):
    """Send via Twilio."""
    try:
        from twilio.rest import Client

        sid = settings.TWILIO_ACCOUNT_SID
        token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_PHONE_NUMBER

        if not all([sid, token, from_number]):
            return {
                'success': False,
                'provider': 'twilio',
                'error': 'Twilio credentials not configured',
            }

        # Normalize Bangladeshi number to +8801XXXXXXXXX
        to_phone = _normalize_bd_phone(to_phone)

        client = Client(sid, token)
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_phone,
        )

        logger.info(f"✅ Twilio SMS sent to {to_phone} (SID: {msg.sid})")
        return {
            'success': True,
            'provider': 'twilio',
            'sid': msg.sid,
            'error': None,
        }

    except Exception as e:
        logger.error(f"❌ Twilio SMS failed: {e}")
        return {'success': False, 'provider': 'twilio', 'error': str(e)}


def _send_sslwireless(to_phone, message):
    """Send via SSL Wireless (Bangladesh)."""
    try:
        import requests

        api_key = settings.SSLWIRELESS_API_KEY
        sender_id = settings.SSLWIRELESS_SENDER_ID
        api_url = settings.SSLWIRELESS_API_URL

        if not api_key:
            return {
                'success': False,
                'provider': 'sslwireless',
                'error': 'SSL Wireless API key not configured',
            }

        # Normalize to 8801XXXXXXXXX (SSL Wireless format)
        phone = _normalize_bd_phone(to_phone).replace('+', '')

        payload = {
            'api_token': api_key,
            'sid': sender_id,
            'msisdn': phone,
            'sms': message,
            'csms_id': f'IB{__import__("uuid").uuid4().hex[:12]}',
        }

        response = requests.post(api_url, json=payload, timeout=10)
        data = response.json()

        if response.status_code == 200 and data.get('status') == 'SUCCESS':
            logger.info(f"✅ SSL Wireless SMS sent to {phone}")
            return {
                'success': True,
                'provider': 'sslwireless',
                'response': data,
                'error': None,
            }
        else:
            logger.warning(f"⚠️ SSL Wireless response: {data}")
            return {
                'success': False,
                'provider': 'sslwireless',
                'error': str(data),
            }

    except Exception as e:
        logger.error(f"❌ SSL Wireless SMS failed: {e}")
        return {'success': False, 'provider': 'sslwireless', 'error': str(e)}


def _send_console(to_phone, message):
    """Console fallback (development)."""
    print(f"\n{'='*60}")
    print(f"📱 SMS to {to_phone}")
    print(f"{'='*60}")
    print(message)
    print(f"{'='*60}\n")
    return {'success': True, 'provider': 'console', 'error': None}


def _normalize_bd_phone(phone):
    """Normalize Bangladeshi phone number."""
    phone = str(phone).strip().replace(' ', '').replace('-', '')
    if phone.startswith('+880'):
        return phone
    if phone.startswith('880'):
        return '+' + phone
    if phone.startswith('01'):
        return '+88' + phone
    return phone