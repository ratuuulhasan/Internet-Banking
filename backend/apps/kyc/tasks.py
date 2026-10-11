"""
Async Celery tasks for KYC OCR processing.
"""
from celery import shared_task
from django.utils import timezone
import traceback

from .models import KYC
from .utils import call_kyc_verification, save_ocr_result


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_kyc_ocr(self, kyc_id: int):
    """
    Async task — process KYC OCR in background.
    Called when user submits KYC.
    """
    try:
        kyc = KYC.objects.get(kyc_id=kyc_id)
    except KYC.DoesNotExist:
        return {'status': 'not_found', 'kyc_id': kyc_id}

    print(f"🔍 Processing KYC #{kyc_id} OCR...")
    kyc.status = 'PROCESSING'
    kyc.save()

    try:
        result = call_kyc_verification(kyc)
        save_ocr_result(kyc, result)

        if result['success']:
            print(f"✅ KYC #{kyc_id} OCR complete — {kyc.ocr_fields_extracted} fields")
            return {
                'status': 'success',
                'kyc_id': kyc_id,
                'fields_extracted': kyc.ocr_fields_extracted,
                'auto_approve': kyc.auto_approve,
            }
        else:
            print(f"❌ KYC #{kyc_id} OCR failed: {result.get('error')}")
            return {'status': 'failed', 'kyc_id': kyc_id, 'error': result.get('error')}

    except Exception as e:
        tb = traceback.format_exc()
        print(f"❌ KYC #{kyc_id} exception: {tb}")
        kyc.status = 'PENDING'
        kyc.ocr_error = str(e)
        kyc.save()

        # Retry
        raise self.retry(exc=e)