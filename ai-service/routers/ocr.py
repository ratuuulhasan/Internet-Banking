"""
OCR Router — NID extraction + verification endpoints.
"""
import base64
import traceback
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from ocr.nid_extractor import extract_text, parse_nid
from ocr.image_preprocess import preprocess_nid
from ocr.validators import full_validation
from ocr.tamper_detector import detect_tampering
from ocr.face_matcher import match_faces

router = APIRouter()


# ============ SCHEMAS ============

class Base64ImageRequest(BaseModel):
    image_base64: str          # data:image/png;base64,... or raw base64


class Base64KYCFrontRequest(BaseModel):
    nid_front_base64: str
    nid_back_base64: Optional[str] = None
    selfie_base64: Optional[str] = None


# ============ HELPERS ============

def decode_base64_image(b64: str) -> bytes:
    """Accept both data URL and raw base64."""
    if ',' in b64 and b64.startswith('data:'):
        b64 = b64.split(',', 1)[1]
    try:
        return base64.b64decode(b64)
    except Exception as e:
        raise HTTPException(400, f"Invalid base64 image: {e}")


# ============ ENDPOINTS ============

@router.post("/extract-nid")
async def extract_nid(file: UploadFile = File(...)):
    """
    Extract structured data from a single NID image (multipart upload).
    Returns text, parsed fields, tamper score, validation.
    """
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(400, "File must be an image")

    try:
        image_bytes = await file.read()
        return _run_extract_nid(image_bytes)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Extraction error: {str(e)}")


@router.post("/extract-nid-base64")
async def extract_nid_base64(req: Base64ImageRequest):
    """Same as /extract-nid but accepts JSON with base64 image."""
    try:
        image_bytes = decode_base64_image(req.image_base64)
        return _run_extract_nid(image_bytes)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Extraction error: {str(e)}")


def _run_extract_nid(image_bytes: bytes) -> dict:
    """Core extraction pipeline — reused by both endpoints."""
    processed = preprocess_nid(image_bytes)
    extracted = extract_text(processed['deskewed'])
    print(f"📄 Extracted {len(extracted)} text regions")

    parsed = parse_nid(extracted)
    validation = full_validation(parsed)
    tamper = detect_tampering(image_bytes)

    return {
        'success': True,
        'ocr': parsed,
        'validation': validation,
        'tamper': tamper,
        'extracted_count': len(extracted),
    }


@router.post("/verify-kyc")
async def verify_kyc(
    nid_front: UploadFile = File(...),
    nid_back: Optional[UploadFile] = File(None),
    selfie: Optional[UploadFile] = File(None),
):
    """
    Full KYC verification (multipart):
    1. Extract NID data (front + back)
    2. Validate format / DOB
    3. Tamper detection (front + back)
    4. Face match (NID photo vs selfie)
    """
    try:
        nid_front_bytes = await nid_front.read()
        nid_back_bytes = await nid_back.read() if nid_back else None
        selfie_bytes = await selfie.read() if selfie else None

        return _run_verify_kyc(nid_front_bytes, nid_back_bytes, selfie_bytes)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Verification error: {str(e)}")


@router.post("/verify-kyc-base64")
async def verify_kyc_base64(req: Base64KYCFrontRequest):
    """Same as /verify-kyc but accepts JSON + base64."""
    try:
        nid_front_bytes = decode_base64_image(req.nid_front_base64)
        nid_back_bytes = (
            decode_base64_image(req.nid_back_base64)
            if req.nid_back_base64 else None
        )
        selfie_bytes = (
            decode_base64_image(req.selfie_base64)
            if req.selfie_base64 else None
        )
        return _run_verify_kyc(nid_front_bytes, nid_back_bytes, selfie_bytes)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Verification error: {str(e)}")


def _run_verify_kyc(nid_front_bytes: bytes,
                    nid_back_bytes: Optional[bytes],
                    selfie_bytes: Optional[bytes]) -> dict:
    """Core verification pipeline."""
    # ---- Front ----
    processed_front = preprocess_nid(nid_front_bytes)
    extracted_front = extract_text(processed_front['deskewed'])
    parsed_front = parse_nid(extracted_front)
    validation = full_validation(parsed_front)
    tamper_front = detect_tampering(nid_front_bytes)

    # ---- Back ----
    parsed_back = {}
    tamper_back = {}
    if nid_back_bytes:
        processed_back = preprocess_nid(nid_back_bytes)
        extracted_back = extract_text(processed_back['deskewed'])
        parsed_back = parse_nid(extracted_back)
        tamper_back = detect_tampering(nid_back_bytes)

    # ---- Face match ----
    face = {}
    if selfie_bytes:
        face = match_faces(nid_front_bytes, selfie_bytes)

    # ---- Checks ----
    checks = {
        'validation_passed': validation.get('passed', False),
        'front_not_tampered': not tamper_front.get('is_tampered', False),
        'back_not_tampered': (
            not tamper_back.get('is_tampered', False)
            if tamper_back else True
        ),
        'face_matched': (
            face.get('match', False) if face else None
        ),
    }

    passed = sum(1 for v in checks.values() if v is True or v is None)
    total = sum(1 for v in checks.values() if v is not None)
    score = passed / total if total else 0

    auto_approve = (
        checks['validation_passed']
        and checks['front_not_tampered']
        and (face.get('match', False) if face else True)
    )

    return {
        'success': True,
        'auto_approve': auto_approve,
        'verification_score': round(score, 4),
        'checks': checks,
        'nid_front': {
            'ocr': parsed_front,
            'validation': validation,
            'tamper': tamper_front,
        },
        'nid_back': {
            'ocr': parsed_back,
            'tamper': tamper_back,
        } if parsed_back else None,
        'face_match': face,
        'needs_manual_review': not auto_approve,
    }


@router.get("/health")
def ocr_health():
    """
    OCR service health — checks if EasyOCR & face_recognition are available.
    """
    from ocr.nid_extractor import _reader
    from ocr.face_matcher import FACE_RECOGNITION_AVAILABLE

    return {
        'status': 'ok',
        'easyocr_loaded': _reader is not None,
        'face_recognition_available': FACE_RECOGNITION_AVAILABLE,
        'endpoints': [
            'POST /ocr/extract-nid',
            'POST /ocr/extract-nid-base64',
            'POST /ocr/verify-kyc',
            'POST /ocr/verify-kyc-base64',
            'GET  /ocr/health',
        ],
    }