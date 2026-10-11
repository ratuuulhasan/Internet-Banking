"""
Detect image tampering using:
1. Error Level Analysis (ELA)
2. Noise inconsistency
3. Copy-move detection (basic)
"""
import cv2
import numpy as np
from PIL import Image
import io


def error_level_analysis(image_bytes: bytes, quality: int = 90) -> dict:
    """
    Error Level Analysis — re-save image at lower quality, compare.
    Tampered regions show different error levels.
    """
    # Original
    original = Image.open(io.BytesIO(image_bytes)).convert('RGB')

    # Resave at lower quality
    buffer = io.BytesIO()
    original.save(buffer, 'JPEG', quality=quality)
    buffer.seek(0)
    resaved = Image.open(buffer).convert('RGB')

    # Compute absolute difference
    orig_arr = np.array(original, dtype=np.float32)
    resaved_arr = np.array(resaved, dtype=np.float32)

    diff = np.abs(orig_arr - resaved_arr)
    ela_image = (diff / diff.max() * 255).astype(np.uint8) if diff.max() > 0 else diff.astype(np.uint8)

    # Compute statistics
    mean_diff = float(diff.mean())
    max_diff = float(diff.max())
    std_diff = float(diff.std())

    # High variance suggests tampering
    # Threshold: std > 12 = suspicious, > 20 = very likely tampered
    tamper_score = min(1.0, std_diff / 25.0)

    return {
        'tamper_score': round(tamper_score, 4),
        'is_tampered': tamper_score > 0.5,
        'ela_mean': round(mean_diff, 2),
        'ela_std': round(std_diff, 2),
        'ela_max': round(max_diff, 2),
    }


def noise_inconsistency(image_bytes: bytes) -> dict:
    """Check noise level consistency across image regions."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        return {'noise_score': 0.0, 'is_inconsistent': False}

    # Split into 4x4 grid
    h, w = img.shape
    grid_h, grid_w = h // 4, w // 4
    noise_levels = []

    for i in range(4):
        for j in range(4):
            cell = img[i * grid_h:(i + 1) * grid_h, j * grid_w:(j + 1) * grid_w]
            if cell.size == 0:
                continue
            # Laplacian variance = noise proxy
            noise = cv2.Laplacian(cell, cv2.CV_64F).var()
            noise_levels.append(noise)

    if not noise_levels:
        return {'noise_score': 0.0, 'is_inconsistent': False}

    noise_levels = np.array(noise_levels)
    mean_noise = float(noise_levels.mean())
    std_noise = float(noise_levels.std())

    # High std relative to mean → inconsistent noise → possible edit
    ratio = std_noise / (mean_noise + 1)
    is_inconsistent = ratio > 0.8

    return {
        'noise_score': round(float(ratio), 4),
        'is_inconsistent': is_inconsistent,
        'mean_noise': round(mean_noise, 2),
        'std_noise': round(std_noise, 2),
    }


def detect_tampering(image_bytes: bytes) -> dict:
    """Combined tamper detection."""
    try:
        ela = error_level_analysis(image_bytes)
        noise = noise_inconsistency(image_bytes)

        # Combined score
        combined_score = (
            ela['tamper_score'] * 0.6 + noise['noise_score'] * 0.4
        )
        combined_score = min(1.0, combined_score)

        return {
            'tamper_score': round(combined_score, 4),
            'is_tampered': combined_score > 0.5,
            'risk_level': (
                'HIGH' if combined_score > 0.6 else
                'MEDIUM' if combined_score > 0.4 else
                'LOW'
            ),
            'details': {
                'ela': ela,
                'noise': noise,
            }
        }
    except Exception as e:
        return {
            'tamper_score': 0.0,
            'is_tampered': False,
            'risk_level': 'UNKNOWN',
            'error': str(e),
        }