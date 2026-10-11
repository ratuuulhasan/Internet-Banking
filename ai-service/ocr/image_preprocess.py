"""
Image preprocessing for OCR — improves accuracy significantly.
"""
import cv2
import numpy as np


def preprocess_nid(image_bytes: bytes) -> dict:
    """
    Preprocess NID image for better OCR.
    Returns:
        {
            'grayscale': np.ndarray,
            'threshold': np.ndarray,
            'denoised': np.ndarray,
            'deskewed': np.ndarray,
        }
    """
    # Decode image
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image")

    # Resize if too small (OCR needs min ~300 DPI equivalent)
    h, w = img.shape[:2]
    if max(h, w) < 1200:
        scale = 1200 / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # Adaptive threshold (better than global for varying lighting)
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2,
    )

    # Deskew (correct rotation)
    deskewed = deskew(thresh)

    return {
        'original': img,
        'grayscale': gray,
        'denoised': denoised,
        'threshold': thresh,
        'deskewed': deskewed,
    }


def deskew(image: np.ndarray) -> np.ndarray:
    """Correct slight rotation using Hough transform."""
    try:
        coords = np.column_stack(np.where(image > 0))
        if len(coords) < 100:
            return image

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Only rotate if significant
        if abs(angle) < 0.5 or abs(angle) > 15:
            return image

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated
    except Exception:
        return image


def crop_nid_regions(image: np.ndarray) -> dict:
    """
    Detect NID card boundary and crop regions.
    Bangladesh NID is typically 85.6 x 53.98 mm (ISO/IEC 7810 ID-1).
    Aspect ratio ~1.586
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {'card': image, 'regions': {}}

    # Find largest rectangular contour
    card_contour = None
    max_area = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area < 10000:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and area > max_area:
            max_area = area
            card_contour = approx

    if card_contour is None:
        return {'card': image, 'regions': {}}

    x, y, w, h = cv2.boundingRect(card_contour)
    card = image[y:y + h, x:x + w]

    # Approximate region splits (Bangladesh NID layout)
    # Top-left: photo, top-right: NID number, middle: name, bottom: address
    regions = {
        'photo': card[int(h * 0.15):int(h * 0.75), int(w * 0.55):int(w * 0.75)],
        'nid_number': card[int(h * 0.30):int(h * 0.55), int(w * 0.02):int(w * 0.65)],
        'name_bn': card[int(h * 0.15):int(h * 0.35), int(w * 0.02):int(w * 0.55)],
        'name_en': card[int(h * 0.30):int(h * 0.50), int(w * 0.02):int(w * 0.55)],
    }

    return {'card': card, 'regions': regions, 'bbox': (x, y, w, h)}