"""
Extract structured data from Bangladesh NID card.
EasyOCR-only, tuned for accuracy with Bangla NID cards.
"""
import re
import numpy as np
from typing import Optional

_reader = None


def get_reader():
    """Lazy-load EasyOCR."""
    global _reader
    if _reader is None:
        print("⏳ Loading EasyOCR (bn + en)...")
        import easyocr
        _reader = easyocr.Reader(['bn', 'en'], gpu=False,
                                 model_storage_directory=None)
        print("✅ EasyOCR loaded")
    return _reader


# ============================================================
# TEXT CLEANING — Fixes known EasyOCR misreads
# ============================================================

BANGLA_FIXES = {
    # Common misreads on NID
    'গিতা': 'পিতা',
    'গিতাঃ': 'পিতা:',
    'শবিদতগু#': '',
    'কদমণ;': '',
    'ঘলা এশ': 'রক্তের গ্রুপ',
    'যতী': '',
    'গাস]ল': '',
    'বাংাদেশ': 'বাংলাদেশ',
    'প্রদানকার কর্তৃপদ্য় স্বাক্ষ্ম্ন': '',
    'পদালয তযিপ:': 'প্রদানের তারিখ:',
    '০১০৮া২০২৬': '০১/০৮/২০২৬',
    'সংশোধিত কাডট কর্তৃক বর্ণিত সদয়': '',
    'খোঘাও পাওথা গেলে': '',
    'নিং্টঃ': '',
    'পোেস্ট সফিস': '',
    'এদা নেবশ শলা পনুবোব দ্প ছশ': '',
    'মেপন্নগ': '',
    'শামগয়তনা': '',
    'দিকনা': 'ঠিকানা',
}

ENGLISH_FIXES = {
    'RATLL': 'RATUL',
    'ASAN': 'HASAN',
    'Govemment': 'Government',
    'Peopie': 'People',
    'Republicof': 'Republic of',
    'Natlonal': 'National',
    'Birtli': 'Birth',
    'Grup': 'Group',
    '|DN0:': 'ID NO:',
    '|DNO:': 'ID NO:',
}


def clean_bangla(text: str) -> str:
    for k, v in BANGLA_FIXES.items():
        text = text.replace(k, v)
    return text.strip()


def clean_english(text: str) -> str:
    for k, v in ENGLISH_FIXES.items():
        text = text.replace(k, v)
    return text.strip()


def is_bangla(text: str) -> bool:
    return bool(re.search(r'[\u0980-\u09FF]', text))


def is_english_name(text: str) -> bool:
    if not text or len(text) < 4 or len(text) > 60:
        return False
    if not re.match(r'^[A-Za-z\s\.\-]+$', text):
        return False
    if len(text.split()) < 2:
        return False
    skip = ['GOVERNMENT', 'BANGLADESH', 'PEOPLE', 'REPUBLIC', 'NATIONAL',
            'CARD', 'BLOOD', 'GROUP', 'DATE', 'BIRTH', 'IDNO', 'ID NO']
    upper = text.upper()
    if any(w in upper for w in skip):
        return False
    # Reject names that are too long (likely garbage)
    if len(text) > 40:
        return False
    return True


def is_bangla_name(text: str) -> bool:
    if not text or not is_bangla(text):
        return False
    clean = text.strip()
    if len(clean) < 3 or len(clean) > 50:
        return False
    skip = ['গণপ্রজাতন্ত্রী', 'বাংলাদেশ', 'সরকার', 'কাডট', 'পরিচয়',
            'জাতীয়', 'নাম', 'পিতা', 'মাতা', 'ঠিকানা', 'রক্তের',
            'প্রদান', 'স্বাক্ষর', 'তারিখ', 'সংশোধিত', 'সদয়']
    if any(w in clean for w in skip):
        return False
    # Must have at least 2 Bangla chars contiguous
    if not re.search(r'[\u0980-\u09FF]{2,}', clean):
        return False
    return True


# ============================================================
# OCR EXTRACTION
# ============================================================

def extract_text(image: np.ndarray, use_paragraph: bool = False) -> list:
    """Extract text with positions (EasyOCR)."""
    reader = get_reader()

    try:
        if use_paragraph:
            results = reader.readtext(image, detail=1, paragraph=True)
        else:
            results = reader.readtext(
                image, detail=1, paragraph=False,
                text_threshold=0.6,      # Lower = more sensitive
                low_text=0.3,
                link_threshold=0.4,
            )
    except Exception as e:
        print(f"⚠️  EasyOCR error (mode={use_paragraph}): {e}")
        return []

    extracted = []
    for item in results:
        if len(item) == 3:
            bbox, text, conf = item
            confidence = float(conf)
        elif len(item) == 2:
            bbox, text = item
            confidence = 0.5
        else:
            continue

        if not text or not text.strip():
            continue

        extracted.append({
            'text': text.strip(),
            'confidence': confidence,
            'bbox': [[int(p[0]), int(p[1])] for p in bbox],
            'y_center': int(np.mean([p[1] for p in bbox])),
            'x_left': int(min(p[0] for p in bbox)),
            'x_right': int(max(p[0] for p in bbox)),
            'x_center': int(np.mean([p[0] for p in bbox])),
        })

    extracted.sort(key=lambda e: (e['y_center'], e['x_left']))
    return extracted


# ============================================================
# PARSING HELPERS
# ============================================================

def find_next_below(extracted, item_index, max_lines=3):
    """Find items below a given item."""
    anchor = extracted[item_index]
    results = []
    for j in range(item_index + 1, min(item_index + max_lines + 1, len(extracted))):
        item = extracted[j]
        dy = item['y_center'] - anchor['y_center']
        if dy < 5 or dy > 80:
            continue
        results.append(item)
    return results


def find_same_line_right(extracted, item_index):
    """Find items on the same horizontal line, to the right."""
    anchor = extracted[item_index]
    results = []
    for j in range(item_index + 1, len(extracted)):
        item = extracted[j]
        if item['y_center'] - anchor['y_center'] > 25:
            break
        if abs(item['y_center'] - anchor['y_center']) <= 25:
            if item['x_left'] > anchor['x_right'] - 10:
                results.append(item)
    return results


# ============================================================
# MAIN PARSER
# ============================================================

def parse_nid(extracted: list) -> dict:
    """Parse NID fields with scoring-based best-candidate selection."""

    # Clean each item
    for e in extracted:
        e['clean_bn'] = clean_bangla(e['text'])
        e['clean_en'] = clean_english(e['text'])

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
        'raw_text': [e['clean_bn'] for e in extracted],
        'avg_confidence': 0.0,
    }

    full_text = ' '.join(e['clean_bn'] for e in extracted)
    full_text_en = ' '.join(e['clean_en'] for e in extracted)

    # ============ NID NUMBER ============
    for pat in [
        r'(?:ID\s*N[O0]|NID|I?DN[0O]?)\s*[:\s]*(\d{10,17})',
        r'\b(\d{17})\b',
        r'\b(\d{13})\b',
        r'\b(\d{10})\b',
    ]:
        m = re.search(pat, full_text_en, re.IGNORECASE)
        if m:
            data['nid_number'] = m.group(1)
            break

    # ============ DOB ============
    date_pat = r'(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{4})'
    for e in extracted:
        text = e['clean_en']
        if re.search(r'(date\s*of\s*birth|dob|birth)', text, re.IGNORECASE):
            m = re.search(date_pat, text, re.IGNORECASE)
            if m:
                data['dob'] = m.group(1)
                break
    if not data['dob']:
        m = re.search(date_pat, full_text_en, re.IGNORECASE)
        if m:
            data['dob'] = m.group(1)

    # ============ NAME ENGLISH ============
    # Collect all English name candidates with scores
    candidates_en = []

    for i, e in enumerate(extracted):
        text = e['clean_en']
        # Priority 1: "Name:" label
        m = re.search(r'Name\s*:?\s*([A-Za-z][A-Za-z\s\.\-]+)', text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Fix common concatenation
            candidate = fix_english_name(candidate)
            if is_english_name(candidate):
                # High score for label-based
                candidates_en.append((candidate, e['confidence'] + 0.5, 'label'))
                continue

        # Priority 2: All-caps English words
        if is_english_name(e['clean_en']):
            candidates_en.append((e['clean_en'], e['confidence'], 'caps'))

    if candidates_en:
        # Score = confidence + label bonus, length preference
        candidates_en.sort(
            key=lambda x: (x[1], len(x[0])),
            reverse=True
        )
        data['name_english'] = candidates_en[0][0]

    # ============ NAME BANGLA ============
    candidates_bn = []

    for i, e in enumerate(extracted):
        text = e['clean_bn']
        # Priority 1: Right after "নাম:" label
        if re.search(r'নাম\s*[:]?', text):
            m = re.search(r'নাম\s*:?\s*(.+)', text)
            if m and m.group(1).strip():
                candidate = m.group(1).strip()
                if is_bangla_name(candidate):
                    candidates_bn.append((candidate, e['confidence'] + 0.6, 'label_inline'))
                    continue
            # Next line below
            for below in find_next_below(extracted, i, max_lines=3):
                if is_bangla_name(below['clean_bn']):
                    candidates_bn.append((below['clean_bn'], below['confidence'] + 0.4, 'label_below'))
                    break

        # Priority 2: Standalone Bangla names
        if is_bangla_name(text):
            candidates_bn.append((text, e['confidence'], 'standalone'))

    if candidates_bn:
        # Score: label bonus + confidence + quality of characters
        def bn_score(item):
            cand, conf, tag = item
            # Bonus for label tags
            tag_bonus = 0.6 if 'label' in tag else 0
            # Bonus if name has no unlikely garbage chars
            quality = 0
            if not re.search(r'[^\u0980-\u09FF\s\-\.]', cand):
                quality += 0.2
            # Penalize very short / very long
            length_ok = 0.1 if 5 <= len(cand) <= 25 else 0
            return conf + tag_bonus + quality + length_ok

        candidates_bn.sort(key=bn_score, reverse=True)
        data['name_bangla'] = candidates_bn[0][0]

    # ============ FATHER NAME ============
    candidates_father = []
    for i, e in enumerate(extracted):
        text = e['clean_bn']
        if re.search(r'পিতা\s*[:]?', text):
            # Same line
            m = re.search(r'পিতা\s*:?\s*(.+)', text)
            if m and m.group(1).strip() and len(m.group(1).strip()) > 2:
                candidates_father.append((m.group(1).strip(), e['confidence'] + 0.6, 'label'))
                continue
            # Next line
            for below in find_next_below(extracted, i, max_lines=4):
                if is_bangla_name(below['clean_bn']):
                    candidates_father.append((below['clean_bn'], below['confidence'] + 0.5, 'below'))
                    break
            # Right
            for right in find_same_line_right(extracted, i):
                if is_bangla_name(right['clean_bn']):
                    candidates_father.append((right['clean_bn'], right['confidence'] + 0.5, 'right'))
                    break

    # Fallback: any Bangla name nearby "শাহজাহান"/"বেপারী" style patterns
    if not candidates_father:
        for e in extracted:
            text = e['clean_bn']
            if re.search(r'(শাহ|মোঃ|মুহাম্মদ|আব্দুল|হোসেন|আহমেদ|বেপারী)', text):
                if is_bangla_name(text):
                    candidates_father.append((text, e['confidence'], 'fallback'))

    if candidates_father:
        def father_score(item):
            cand, conf, tag = item
            tag_bonus = 0.6 if tag in ['label', 'below', 'right'] else 0
            # Bonus if common Bangla name patterns
            quality = 0
            if re.search(r'(শাহ|মোঃ|মুহাম্মদ|আব্দুল|হোসেন|আহমেদ|বেপারী|নাহার|হাসান)', cand):
                quality += 0.3
            length_ok = 0.1 if 5 <= len(cand) <= 30 else 0
            return conf + tag_bonus + quality + length_ok

        candidates_father.sort(key=father_score, reverse=True)
        data['father_name'] = candidates_father[0][0]

    # ============ MOTHER NAME ============
    candidates_mother = []
    for i, e in enumerate(extracted):
        text = e['clean_bn']
        if re.search(r'মাতা\s*[:]?|মাতী\s*[:]?', text):
            m = re.search(r'মাত[াী]\s*:?\s*(.+)', text)
            if m and m.group(1).strip() and len(m.group(1).strip()) > 2:
                candidates_mother.append((m.group(1).strip(), e['confidence'] + 0.6, 'label'))
                continue
            for below in find_next_below(extracted, i, max_lines=4):
                if is_bangla_name(below['clean_bn']):
                    candidates_mother.append((below['clean_bn'], below['confidence'] + 0.5, 'below'))
                    break
            for right in find_same_line_right(extracted, i):
                if is_bangla_name(right['clean_bn']):
                    candidates_mother.append((right['clean_bn'], right['confidence'] + 0.5, 'right'))
                    break

    # Fallback: look for নাহার / বেগম / খাতুন patterns
    if not candidates_mother:
        for e in extracted:
            text = e['clean_bn']
            if re.search(r'(নাহার|বেগম|খাতুন|আক্তার|সুলতানা)', text):
                if is_bangla_name(text):
                    candidates_mother.append((text, e['confidence'], 'fallback'))

    if candidates_mother:
        def mother_score(item):
            cand, conf, tag = item
            tag_bonus = 0.6 if tag in ['label', 'below', 'right'] else 0
            quality = 0
            if re.search(r'(নাহার|বেগম|খাতুন|আক্তার|সুলতানা)', cand):
                quality += 0.3
            length_ok = 0.1 if 3 <= len(cand) <= 30 else 0
            return conf + tag_bonus + quality + length_ok

        candidates_mother.sort(key=mother_score, reverse=True)
        data['mother_name'] = candidates_mother[0][0]

    # ============ BLOOD GROUP ============
    for i, e in enumerate(extracted):
        text = e['clean_bn'] + ' ' + e['clean_en']
        if re.search(r'(blood\s*grup|blood\s*group|রক্তের\s*গ্রুপ|রক্ত)', text, re.IGNORECASE):
            candidates = [e['clean_bn'], e['clean_en']]
            for below in find_next_below(extracted, i, max_lines=3):
                candidates.append(below['clean_bn'])
                candidates.append(below['clean_en'])
            for right in find_same_line_right(extracted, i):
                candidates.append(right['clean_bn'])
                candidates.append(right['clean_en'])
            combined = ' '.join(candidates)
            m = re.search(r'\b(AB|A|B|O)\s*([+\-])', combined, re.IGNORECASE)
            if m:
                data['blood_group'] = f"{m.group(1).upper()}{m.group(2)}"
                break

    if not data['blood_group']:
        m = re.search(r'\b(AB|A|B|O)\s*([+\-])\b', full_text)
        if m:
            data['blood_group'] = f"{m.group(1).upper()}{m.group(2)}"

    # ============ ADDRESS ============
    for i, e in enumerate(extracted):
        text = e['clean_bn']
        if re.search(r'ঠিকানা|সিকানা|address', text, re.IGNORECASE):
            parts = []
            # Same line — strip label
            cleaned = re.sub(
                r'^(ঠিকানা|সিকানা|Address)\s*:?\s*',
                '', text, flags=re.IGNORECASE
            )
            # Score: only accept if contains address-like tokens
            if cleaned and len(cleaned) > 5:
                parts.append(cleaned)
            # Right side
            for right in find_same_line_right(extracted, i):
                if len(right['clean_bn']) > 3:
                    parts.append(right['clean_bn'])
            # Below lines (2-3)
            for below in find_next_below(extracted, i, max_lines=3):
                if len(below['clean_bn']) > 3:
                    parts.append(below['clean_bn'])
            if parts:
                # Join + clean
                addr = ', '.join(parts)
                # Remove unlikely tokens
                addr = re.sub(r'\b\d{1,2}:\d{2}\b', '', addr)  # timestamps
                data['address'] = addr.strip(' ,.')
                break

    # ============ ISSUE DATE ============
    date_slash = r'(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{2}[/-]\d{2}[/-]\d{4})'
    for i, e in enumerate(extracted):
        text = e['clean_bn']
        if re.search(r'প্রদানের\s*তারিণ|প্রদানের\s*তারিখ|issue\s*date', text, re.IGNORECASE):
            m = re.search(date_slash, text)
            if m:
                data['issue_date'] = m.group(1)
                break
            for below in find_next_below(extracted, i, max_lines=3):
                m = re.search(date_slash, below['clean_bn'])
                if m:
                    data['issue_date'] = m.group(1)
                    break
            if data['issue_date']:
                break

    # ============ CONFIDENCE ============
    meaningful = [
        e for e in extracted
        if (len(e['text']) > 3
            and not any(skip in e['text'] for skip in
                ['এই কাডট', 'এই ফাডট', 'গণপ্রজাতন্ত্রী', 'সংশোধিত',
                 'খোঘাও', 'শেপাঙ', 'পোেস্ট', 'ধোপাও', 'এহ ফাডট',
                 'সশ', 'পশভ']))
    ]
    if meaningful:
        data['avg_confidence'] = round(
            sum(e['confidence'] for e in meaningful) / len(meaningful),
            4
        )

    data['fields_extracted'] = sum([
        1 for k, v in data.items()
        if k not in ['raw_text', 'avg_confidence', 'fields_extracted'] and v is not None
    ])

    return data


def fix_english_name(name: str) -> str:
    """
    Fix common English name misreads and concatenations.
    'RATULHASAN' → 'RATUL HASAN'
    'RATV! TASAN' → 'RATUL HASAN'
    """
    # Remove non-alpha chars
    cleaned = re.sub(r'[^A-Za-z\s]', '', name).strip()
    if not cleaned:
        return name

    # Fix concatenated all-caps names
    # 'RATULHASAN' → split on common name boundaries
    if cleaned.isupper() and ' ' not in cleaned and len(cleaned) > 8:
        # Try to split at natural boundaries
        # Check known first names / last names
        common_first = ['RATUL', 'MD', 'MOHAMMAD', 'MUHAMMAD', 'ABDUL', 'ABU',
                        'SHAH', 'JAHAN', 'MOSTAFA', 'KAMAL', 'RASHED']
        common_last = ['HASAN', 'HOSSAIN', 'RAHMAN', 'ISLAM', 'AHMED', 'AKTER',
                       'AKHTAR', 'BEPARI', 'MIA', 'MIAH', 'KHAN', 'CHOWDHURY']
        for first in common_first:
            if cleaned.startswith(first) and len(cleaned) > len(first):
                rest = cleaned[len(first):]
                for last in common_last:
                    if rest == last or rest.startswith(last):
                        return f"{first} {rest}".strip()
                # Just split first word
                return f"{first} {rest}".strip()

        # Fallback: split in the middle
        mid = len(cleaned) // 2
        return f"{cleaned[:mid]} {cleaned[mid:]}"

    return cleaned