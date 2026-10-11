"""
Extract structured data from Bangladesh NID card.
Supports both Bangla and English NIDs.
"""
import re
import easyocr
import numpy as np
from typing import Optional

_reader = None


def get_reader():
    """Lazy-load EasyOCR (Bangla + English)."""
    global _reader
    if _reader is None:
        print("⏳ Loading EasyOCR model (bn + en)...")
        _reader = easyocr.Reader(['bn', 'en'], gpu=False)
        print("✅ EasyOCR loaded")
    return _reader


def extract_text(image: np.ndarray) -> list:
    """
    Extract all text from image with positions.
    Returns: [{'text': str, 'conf': float, 'bbox': [[x,y],...]}]
    """
    reader = get_reader()
    results = reader.readtext(image, detail=1, paragraph=False)

    extracted = []
    for bbox, text, conf in results:
        extracted.append({
            'text': text.strip(),
            'confidence': float(conf),
            'bbox': [[int(p[0]), int(p[1])] for p in bbox],
        })
    return extracted


def parse_nid(extracted: list) -> dict:
    """
    Parse extracted text into structured NID fields.
    """
    data = {
        'nid_number': None,
        'name_bangla': None,
        'name_english': None,
        'father_name': None,
        'mother_name': None,
        'dob': None,
        'blood_group': None,
        'address': None,
        'issue_date': None,
        'raw_text': [e['text'] for e in extracted],
    }

    full_text = ' '.join([e['text'] for e in extracted])
    full_text_en = full_text

    # ---- NID Number ----
    # Bangladesh NID: 10, 13, or 17 digits
    # Look for numeric sequences near "NID" / "No" / "ID"
    nid_patterns = [
        r'\b\d{17}\b',      # 17-digit (older)
        r'\b\d{13}\b',      # 13-digit
        r'\b\d{10}\b',      # 10-digit (new smart NID)
    ]
    for pat in nid_patterns:
        matches = re.findall(pat, full_text)
        if matches:
            # Prefer numbers near "NID" keyword
            for m in matches:
                idx = full_text.find(m)
                context = full_text[max(0, idx - 30):idx].lower()
                if any(k in context for k in ['nid', 'id no', 'no:', 'নং']):
                    data['nid_number'] = m
                    break
            if not data['nid_number']:
                data['nid_number'] = matches[0]
            break

    # ---- Name (English) ----
    # Look for "Name" keyword
    for e in extracted:
        text = e['text']
        # If text contains "Name" keyword
        if re.search(r'\bname\b', text, re.IGNORECASE) and e['confidence'] > 0.4:
            # Try to extract after "Name"
            parts = re.split(r'name\s*:?\s*', text, flags=re.IGNORECASE)
            if len(parts) > 1 and parts[1].strip():
                data['name_english'] = parts[1].strip()
                break

    # Fallback: look for capitalized English words
    if not data['name_english']:
        for e in extracted:
            text = e['text']
            if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$', text) and len(text) > 5:
                data['name_english'] = text
                break

    # ---- Name (Bangla) ----
    # Bangla Unicode block: \u0980-\u09FF
    bangla_pattern = re.compile(r'[\u0980-\u09FF]+')
    for e in extracted:
        text = e['text']
        if bangla_pattern.search(text) and len(text) > 3:
            # Skip common labels
            if any(label in text for label in ['নাম', 'পিতা', 'মাতা', 'ঠিকানা', 'জন্ম']):
                continue
            if not data['name_bangla']:
                data['name_bangla'] = text
                break

    # ---- Father's Name ----
    for e in extracted:
        text = e['text']
        if re.search(r'father|পিতা', text, re.IGNORECASE):
            parts = re.split(r'(father|পিতা)\s*:?\s*', text, flags=re.IGNORECASE)
            if len(parts) > 2 and parts[2].strip():
                data['father_name'] = parts[2].strip()
                break

    # ---- Mother's Name ----
    for e in extracted:
        text = e['text']
        if re.search(r'mother|মাতা', text, re.IGNORECASE):
            parts = re.split(r'(mother|মাতা)\s*:?\s*', text, flags=re.IGNORECASE)
            if len(parts) > 2 and parts[2].strip():
                data['mother_name'] = parts[2].strip()
                break

    # ---- Date of Birth ----
    # Formats: DD MMM YYYY, DD/MM/YYYY, DD-MM-YYYY
    dob_patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',
        r'\b(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+(\d{4})\b',
    ]
    for e in extracted:
        text = e['text'].upper()
        if 'DOB' in text or 'জন্ম' in text or 'BIRTH' in text:
            for pat in dob_patterns:
                m = re.search(pat, text)
                if m:
                    data['dob'] = m.group(0)
                    break
            if data['dob']:
                break

    # Fallback: any date pattern
    if not data['dob']:
        for e in extracted:
            for pat in dob_patterns:
                m = re.search(pat, e['text'].upper())
                if m:
                    data['dob'] = m.group(0)
                    break
            if data['dob']:
                break

    # ---- Blood Group ----
    bg_pattern = r'\b(A|B|AB|O)[+-]\b'
    m = re.search(bg_pattern, full_text_en)
    if m:
        data['blood_group'] = m.group(0)

    # ---- Address ----
    # Look for "Address" / "ঠিকানা" keyword
    for i, e in enumerate(extracted):
        text = e['text']
        if re.search(r'address|ঠিকানা', text, re.IGNORECASE):
            # Take this + next 2 lines
            addr_parts = []
            parts = re.split(r'(address|ঠিকানা)\s*:?\s*', text, flags=re.IGNORECASE)
            if len(parts) > 2:
                addr_parts.append(parts[2].strip())
            for j in range(i + 1, min(i + 3, len(extracted))):
                addr_parts.append(extracted[j]['text'])
            data['address'] = ', '.join([a for a in addr_parts if a])
            break

    # ---- Issue Date ----
    for e in extracted:
        text = e['text'].upper()
        if 'ISSUE' in text or 'প্রদান' in text:
            for pat in dob_patterns:
                m = re.search(pat, text)
                if m:
                    data['issue_date'] = m.group(0)
                    break
            if data['issue_date']:
                break

    # Confidence: average of all extractions
    data['avg_confidence'] = (
        sum(e['confidence'] for e in extracted) / len(extracted)
        if extracted else 0.0
    )

    return data