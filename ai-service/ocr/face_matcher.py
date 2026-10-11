"""
Face matching between NID photo and selfie.
Uses face_recognition (dlib) if available, else falls back to simple histogram.
"""
import io
import numpy as np
from PIL import Image

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("⚠️  face_recognition not installed — using fallback")


def match_faces(nid_image_bytes: bytes, selfie_bytes: bytes) -> dict:
    """
    Compare NID photo with selfie.
    Returns similarity (0-1) and match boolean.
    """
    if FACE_RECOGNITION_AVAILABLE:
        return _match_with_dlib(nid_image_bytes, selfie_bytes)
    else:
        return _match_fallback(nid_image_bytes, selfie_bytes)


def _match_with_dlib(nid_bytes: bytes, selfie_bytes: bytes) -> dict:
    try:
        # Load images
        nid_img = face_recognition.load_image_file(io.BytesIO(nid_bytes))
        selfie_img = face_recognition.load_image_file(io.BytesIO(selfie_bytes))

        # Get face encodings
        nid_encodings = face_recognition.face_encodings(nid_img)
        selfie_encodings = face_recognition.face_encodings(selfie_img)

        if not nid_encodings:
            return {'match': False, 'similarity': 0.0,
                    'reason': 'No face detected in NID photo'}
        if not selfie_encodings:
            return {'match': False, 'similarity': 0.0,
                    'reason': 'No face detected in selfie'}

        # Compare (take first face from each)
        distance = face_recognition.face_distance(
            [nid_encodings[0]], selfie_encodings[0]
        )[0]

        # Convert distance to similarity (lower distance = higher similarity)
        # Threshold typically 0.6
        similarity = max(0.0, 1.0 - distance)
        match = distance < 0.6

        return {
            'match': match,
            'similarity': round(float(similarity), 4),
            'distance': round(float(distance), 4),
            'threshold': 0.6,
            'method': 'dlib',
        }
    except Exception as e:
        return {'match': False, 'similarity': 0.0, 'error': str(e)}


def _match_fallback(nid_bytes: bytes, selfie_bytes: bytes) -> dict:
    """
    Simple fallback using image histograms.
    NOT accurate — only for when dlib unavailable.
    """
    try:
        import cv2

        nid_arr = cv2.imdecode(np.frombuffer(nid_bytes, np.uint8), cv2.IMREAD_COLOR)
        selfie_arr = cv2.imdecode(np.frombuffer(selfie_bytes, np.uint8), cv2.IMREAD_COLOR)

        if nid_arr is None or selfie_arr is None:
            return {'match': False, 'similarity': 0.0, 'reason': 'Could not decode'}

        # Load face detector
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        # Detect faces
        nid_faces = cascade.detectMultiScale(
            cv2.cvtColor(nid_arr, cv2.COLOR_BGR2GRAY), 1.1, 4
        )
        selfie_faces = cascade.detectMultiScale(
            cv2.cvtColor(selfie_arr, cv2.COLOR_BGR2GRAY), 1.1, 4
        )

        if len(nid_faces) == 0:
            return {'match': False, 'similarity': 0.0, 'reason': 'No face in NID'}
        if len(selfie_faces) == 0:
            return {'match': False, 'similarity': 0.0, 'reason': 'No face in selfie'}

        # Crop first face from each
        (x1, y1, w1, h1) = nid_faces[0]
        (x2, y2, w2, h2) = selfie_faces[0]
        nid_face = cv2.resize(nid_arr[y1:y1 + h1, x1:x1 + w1], (100, 100))
        selfie_face = cv2.resize(selfie_arr[y2:y2 + h2, x2:x2 + w2], (100, 100))

        # Histogram comparison
        hist1 = cv2.calcHist([nid_face], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
        hist2 = cv2.calcHist([selfie_face], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
        cv2.normalize(hist1, hist1)
        cv2.normalize(hist2, hist2)

        similarity = float(cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL))
        similarity = max(0.0, similarity)

        return {
            'match': similarity > 0.4,
            'similarity': round(similarity, 4),
            'method': 'histogram (fallback — NOT accurate)',
            'warning': 'Install face_recognition for real face matching',
        }
    except Exception as e:
        return {'match': False, 'similarity': 0.0, 'error': str(e)}