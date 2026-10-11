"""
KYC Utilities — AI service integration for OCR verification.
"""
import os
import requests
from django.conf import settings


AI_SERVICE_URL = getattr(settings, 'AI_SERVICE_URL', 'http://localhost:9000')


def call_kyc_verification(kyc_obj) -> dict:
    """
    Send KYC documents to AI service for verification.
    
    Args:
        kyc_obj: KYC model instance with document_front, document_back, selfie
    
    Returns:
        {
            'success': True/False,
            'data': {...full AI response...},
            'error': 'message if failed',
        }
    """
    try:
        files = {}
        if kyc_obj.document_front and os.path.exists(kyc_obj.document_front.path):
            files['nid_front'] = open(kyc_obj.document_front.path, 'rb')
        else:
            return {'success': False, 'error': 'NID front image missing'}

        if kyc_obj.document_back and os.path.exists(kyc_obj.document_back.path):
            files['nid_back'] = open(kyc_obj.document_back.path, 'rb')

        if kyc_obj.selfie and os.path.exists(kyc_obj.selfie.path):
            files['selfie'] = open(kyc_obj.selfie.path, 'rb')

        # Call AI service
        response = requests.post(
            f"{AI_SERVICE_URL}/ocr/verify-kyc",
            files=files,
            timeout=120,   # 2 min for OCR + face match
        )

        # Close file handles
        for f in files.values():
            f.close()

        if response.status_code != 200:
            return {
                'success': False,
                'error': f'AI service returned {response.status_code}: {response.text[:300]}',
            }

        return {
            'success': True,
            'data': response.json(),
        }

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'AI service timeout (120s)'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'AI service unavailable — check if running on port 9000'}
    except Exception as e:
        return {'success': False, 'error': f'{type(e).__name__}: {str(e)}'}


def save_ocr_result(kyc_obj, ai_response: dict):
    """Save AI OCR result into KYC model fields."""
    if not ai_response.get('success'):
        kyc_obj.ocr_error = ai_response.get('error', 'Unknown error')
        kyc_obj.status = 'PENDING'
        kyc_obj.save()
        return

    data = ai_response.get('data', {})
    nid_front = data.get('nid_front', {}) or {}
    ocr = nid_front.get('ocr', {}) or {}
    tamper = nid_front.get('tamper', {}) or {}
    face_match = data.get('face_match', {}) or {}

    # Store raw JSON
    kyc_obj.ocr_extracted = data

    # Extracted fields
    kyc_obj.ocr_name_bangla = (ocr.get('name_bangla') or '')[:150]
    kyc_obj.ocr_name_english = (ocr.get('name_english') or '')[:150]
    kyc_obj.ocr_father_name = (ocr.get('father_name') or '')[:150]
    kyc_obj.ocr_mother_name = (ocr.get('mother_name') or '')[:150]
    kyc_obj.ocr_dob = (ocr.get('dob') or '')[:50]
    kyc_obj.ocr_blood_group = (ocr.get('blood_group') or '')[:10]
    kyc_obj.ocr_address = ocr.get('address') or ''
    kyc_obj.ocr_issue_date = (ocr.get('issue_date') or '')[:50]
    kyc_obj.ocr_confidence = ocr.get('avg_confidence')
    kyc_obj.ocr_fields_extracted = ocr.get('fields_extracted', 0)

    # Tamper
    kyc_obj.tamper_score = tamper.get('tamper_score')
    kyc_obj.tamper_risk_level = tamper.get('risk_level', '')
    kyc_obj.is_tampered = tamper.get('is_tampered', False)

    # Face match
    kyc_obj.face_match_similarity = face_match.get('similarity')
    kyc_obj.face_matched = face_match.get('match')

    # Verification decision
    kyc_obj.verification_score = data.get('verification_score')
    kyc_obj.auto_approve = data.get('auto_approve', False)
    kyc_obj.needs_manual_review = data.get('needs_manual_review', True)

    # Auto-approve logic
    if kyc_obj.auto_approve and not kyc_obj.is_tampered:
        kyc_obj.status = 'OCR_DONE'   # Admin needs to give final approval
    else:
        kyc_obj.status = 'OCR_DONE'

    kyc_obj.ocr_error = ''
    kyc_obj.save()

    # Auto-activate user if fully auto-approved
    if kyc_obj.auto_approve and not kyc_obj.is_tampered:
        kyc_obj.user.status = 'ACTIVE'
        kyc_obj.user.save()