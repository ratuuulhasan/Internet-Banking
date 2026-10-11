"""
NID validation logic — format, checksum, consistency.
"""
import re
from datetime import datetime


def validate_nid_format(nid: str) -> dict:
    """Validate Bangladesh NID number format."""
    if not nid:
        return {'valid': False, 'reason': 'NID number missing'}

    nid = nid.strip()

    # Bangladesh NID: 10, 13, or 17 digits
    if not re.match(r'^\d{10}$|^\d{13}$|^\d{17}$', nid):
        return {
            'valid': False,
            'reason': f'Invalid length ({len(nid)}). Must be 10, 13, or 17 digits',
        }

    # 10-digit: first digit cannot be 0
    if len(nid) == 10 and nid[0] == '0':
        return {'valid': False, 'reason': 'NID cannot start with 0'}

    return {'valid': True, 'reason': 'OK'}


def validate_dob(dob_str: str) -> dict:
    """Validate date of birth — must be past, age 18-120."""
    if not dob_str:
        return {'valid': False, 'reason': 'DOB missing'}

    # Try multiple formats
    formats = ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y']
    parsed = None
    for fmt in formats:
        try:
            parsed = datetime.strptime(dob_str.upper(), fmt)
            break
        except ValueError:
            continue

    if not parsed:
        return {'valid': False, 'reason': f'Could not parse DOB: {dob_str}'}

    today = datetime.now()
    age = today.year - parsed.year - (
        (today.month, today.day) < (parsed.month, parsed.day)
    )

    if age < 18:
        return {'valid': False, 'reason': f'Age {age} < 18 (minimum for banking)'}

    if age > 120:
        return {'valid': False, 'reason': f'Age {age} > 120 (suspicious)'}

    return {'valid': True, 'reason': 'OK', 'age': age, 'parsed': parsed.isoformat()}


def validate_confidence(avg_conf: float, threshold: float = 0.6) -> dict:
    """Check if OCR confidence is acceptable."""
    if avg_conf < threshold:
        return {
            'valid': False,
            'reason': f'Low OCR confidence ({avg_conf:.2f} < {threshold}). Upload clearer image',
        }
    return {'valid': True, 'reason': 'OK'}


def full_validation(ocr_data: dict) -> dict:
    """Run all validations."""
    results = {
        'nid': validate_nid_format(ocr_data.get('nid_number')),
        'dob': validate_dob(ocr_data.get('dob')),
        'confidence': validate_confidence(ocr_data.get('avg_confidence', 0)),
    }

    all_valid = all(r['valid'] for r in results.values())

    return {
        'passed': all_valid,
        'checks': results,
        'failed_reasons': [
            f"{k}: {v['reason']}"
            for k, v in results.items() if not v['valid']
        ],
    }