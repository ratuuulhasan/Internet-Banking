"""
Hybrid Fraud Detection:
- Uses full XGBoost model (V1-V28) when available
- Falls back to contextual rule-based scoring in production
- Combines both for final score
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'models')


def load_artifacts():
    """Load full model + fallback to v2 if full not available."""
    artifacts = {}

    # Full model (with V1-V28)
    try:
        artifacts['full_model'] = joblib.load(os.path.join(MODEL_DIR, 'fraud_model_full.pkl'))
        artifacts['full_scaler'] = joblib.load(os.path.join(MODEL_DIR, 'scaler_full.pkl'))
        artifacts['full_threshold'] = joblib.load(os.path.join(MODEL_DIR, 'threshold_full.pkl'))
        with open(os.path.join(MODEL_DIR, 'meta_full.json')) as f:
            artifacts['full_meta'] = json.load(f)
        print(f"✅ Full model loaded (ROC-AUC: {artifacts['full_meta'].get('roc_auc', 0):.4f})")
    except Exception as e:
        print(f"⚠️  Full model not found: {e}")

    return artifacts


ARTIFACTS = load_artifacts()


class TxnFeatures(BaseModel):
    amount: float = Field(..., ge=0)
    hour: int = Field(12, ge=0, le=23)
    txn_type: int = 1
    device_change: int = 0
    location_change: int = 0
    account_age_days: int = 0
    txn_count_24h: int = 1
    avg_amount_24h: float = 0.0
    # Optional: pass V1-V28 if available from core banking
    v_features: list = Field(default_factory=list)


def contextual_risk_score(t: TxnFeatures) -> tuple:
    """
    Rule-based risk scoring for production.
    Returns (score 0-1, reasons list).
    """
    score = 0.0
    reasons = []

    amount = t.amount
    avg = t.avg_amount_24h or amount

    # 1. Amount anomalies
    if amount > avg * 5 and amount > 50000:
        score += 0.25
        reasons.append(f"Amount 5x higher than average ({amount:.0f} vs {avg:.0f})")
    elif amount > avg * 3 and amount > 20000:
        score += 0.15
        reasons.append(f"Amount 3x higher than average")

    if amount > 100000:
        score += 0.15
        reasons.append("Very large amount (>100k)")

    if amount < 10 and amount > 0:
        score += 0.10
        reasons.append("Micro-transaction (possible card testing)")

    # 2. Time anomalies
    if t.hour in [1, 2, 3, 4]:
        score += 0.15
        reasons.append(f"Unusual hour ({t.hour}:00)")

    # 3. Device/Location
    if t.device_change and t.location_change:
        score += 0.20
        reasons.append("Both device AND location changed")
    elif t.device_change:
        score += 0.10
        reasons.append("New device")
    elif t.location_change:
        score += 0.10
        reasons.append("New location")

    # 4. Account age
    if t.account_age_days < 7:
        score += 0.20
        reasons.append(f"New account ({t.account_age_days} days)")
    elif t.account_age_days < 30:
        score += 0.10
        reasons.append("Recently opened account")

    # 5. Velocity
    if t.txn_count_24h > 20:
        score += 0.20
        reasons.append(f"High velocity ({t.txn_count_24h} txns/24h)")
    elif t.txn_count_24h > 10:
        score += 0.10
        reasons.append("Elevated velocity")

    # 6. Combined signals
    if t.device_change and t.location_change and t.account_age_days < 30:
        score += 0.15
        reasons.append("New account + device + location change")

    if amount > 50000 and t.hour in [1, 2, 3, 4, 5]:
        score += 0.15
        reasons.append("Large amount at odd hours")

    return min(1.0, score), reasons


def ml_full_score(t: TxnFeatures) -> tuple:
    """Predict using full XGBoost model (V1-V28)."""
    if 'full_model' not in ARTIFACTS:
        return None, []

    try:
        feature_cols = ARTIFACTS['full_meta']['feature_columns']
        row = {col: 0.0 for col in feature_cols}

        # Fill known features
        row['Amount'] = t.amount
        row['Hour'] = t.hour

        # Fill V1-V28 if provided
        for i, v in enumerate(t.v_features[:28]):
            col = f'V{i+1}'
            if col in row:
                row[col] = float(v)

        df = pd.DataFrame([row])[feature_cols]

        # Scale Amount + Hour
        scaler = ARTIFACTS['full_scaler']
        df[['Amount', 'Hour']] = scaler.transform(df[['Amount', 'Hour']])

        proba = float(ARTIFACTS['full_model'].predict_proba(df)[0, 1])
        return proba, []
    except Exception as e:
        print(f"ML error: {e}")
        return None, []


@router.post("/predict")
def predict_fraud(t: TxnFeatures):
    """
    Hybrid prediction:
    - If v_features provided → use ML model primarily
    - Else → use contextual scoring primarily
    - Final = weighted combination
    """
    if 'full_model' not in ARTIFACTS:
        raise HTTPException(503, "Model not trained. Run train_fraud_full.py")

    # Get ML score
    ml_score, _ = ml_full_score(t)

    # Get contextual score
    ctx_score, reasons = contextual_risk_score(t)

    # Final combination
    if ml_score is not None and len(t.v_features) >= 28:
        # Full data available: ML dominates
        final_score = 0.7 * ml_score + 0.3 * ctx_score
        source = "ML+Context"
    else:
        # Production mode: contextual dominates
        # Use a soft ML prior as backup (weak signal from amount only)
        final_score = 0.6 * ctx_score + 0.4 * (ctx_score * 0.5)
        # Actually simpler: just use contextual
        final_score = ctx_score
        source = "Contextual"

    # Decide
    threshold = ARTIFACTS.get('full_threshold', 0.5)
    # For contextual mode, use fixed 0.5
    if source == "Contextual":
        threshold = 0.5

    is_fraud = final_score >= threshold

    if final_score >= 0.75:
        risk = "HIGH"
    elif final_score >= 0.5:
        risk = "MEDIUM"
    elif final_score >= 0.3:
        risk = "LOW"
    else:
        risk = "SAFE"

    return {
        'fraud_score': round(final_score, 4),
        'ml_score': round(ml_score, 4) if ml_score is not None else None,
        'contextual_score': round(ctx_score, 4),
        'is_fraud': bool(is_fraud),
        'threshold': round(float(threshold), 4),
        'risk_level': risk,
        'reasons': reasons,
        'source': source,
        'model': 'XGBoost-Full + Rules',
    }


@router.get("/model-info")
def model_info():
    if 'full_model' not in ARTIFACTS:
        return {'status': 'not_trained'}
    meta = ARTIFACTS['full_meta']
    return {
        'status': 'ready',
        'model': meta.get('model'),
        'roc_auc': meta.get('roc_auc'),
        'auprc': meta.get('auprc'),
        'threshold': meta.get('threshold'),
        'feature_count': len(meta.get('feature_columns', [])),
        'mode': 'hybrid',
    }