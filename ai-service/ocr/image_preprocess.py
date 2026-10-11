"""
Image preprocessing for OCR — improved for Bangla NID cards.
"""
import cv2
import numpy as np


def preprocess_nid(image_bytes: bytes) -> dict:
    """
    Preprocess NID image for better OCR.
    Heavy processing to handle low-res + glare + tilt.
    """
    # Decode
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image")

    # ---- 1. Aggressive upscale for small images ----
    h, w = img.shape[:2]
    target_w = 2000  # Target width for good OCR
    if w < target_w:
        scale = target_w / w
        img = cv2.resize(img, None, fx=scale, fy=scale,
                         interpolation=cv2.INTER_LANCZOS4)

    # ---- 2. Denoise while preserving edges ----
    denoised = cv2.bilateralFilter(img, 9, 75, 75)

    # ---- 3. Convert to grayscale ----
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

    # ---- 4. Contrast enhancement (CLAHE) ----
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # ---- 5. Sharpen ----
    kernel_sharpen = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1],
    ])
    sharpened = cv2.filter2D(enhanced, -1, kernel_sharpen)

    # ---- 6. Adaptive threshold (dual version) ----
    # Version A: standard adaptive
    thresh_a = cv2.adaptiveThreshold(
        sharpened, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15, C=8,
    )

    # Version B: Otsu's method (global)
    _, thresh_b = cv2.threshold(
        sharpened, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    # ---- 7. Morphological cleanup ----
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh_a, cv2.MORPH_CLOSE, kernel)

    # ---- 8. Deskew ----
    deskewed = deskew(sharpened)

    return {
        'original': img,
        'grayscale': gray,
        'enhanced': enhanced,
        'sharpened': sharpened,
        'threshold': cleaned,       # Used for OCR (main)
        'otsu': thresh_b,           # Alternative
        'deskewed': deskewed,       # Best for OCR
    }


def deskew(image: np.ndarray) -> np.ndarray:
    """Correct rotation."""
    try:
        # Use only dark pixels
        bin_img = cv2.threshold(image, 0, 255,
                                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(bin_img > 0))
        if len(coords) < 100:
            return image

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

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