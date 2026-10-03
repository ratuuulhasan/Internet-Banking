import random
import hashlib
from datetime import timedelta
from django.utils import timezone
from .models import OTPVerification


def generate_otp(user, purpose):
    code = f"{random.randint(100000, 999999)}"
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    OTPVerification.objects.create(
        user=user,
        otp_code_hash=code_hash,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    # TODO: Send via SMS/Email
    print(f"\n🔐 OTP for {user.email} [{purpose}]: {code}\n")
    return code


def verify_otp(user, code, purpose):
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