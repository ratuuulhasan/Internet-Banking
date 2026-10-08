import os
import json
import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 👇 Services
from services.shap_service import shap_service
from services.model_registry import registry

router = APIRouter()

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'models')


# ============================================================
# REGISTRY ACCESSOR (auto hot-reload)
# ============================================================
def get_current():
    """
    Get fresh model artifacts from the registry.
    Auto-reloads if reload.flag changed (i.e. new model activated).
    Returns: (model, scaler, threshold, meta)
    """
    registry.check_reload()
    if not registry.is_loaded:
        registry.load()
    return registry.model, registry.scaler, registry.threshold, registry.meta


# ============================================================
# REQUEST SCHEMA
# ============================================================
class TxnFeatures(BaseModel):
    amount: float = Field(..., ge=0)
    hour: int = Field(12, ge=0, le=23)
    txn_type: int = 1
    device_change: int = 0
    location_change: int = 0
    account_age_days: int = 0
    txn_count_24h: int = 1
    avg_amount_24h: float = 0.0


# ============================================================
# FEATURE BUILDER (takes scaler + meta explicitly)
# ============================================================
def build_feature_vector(t: TxnFeatures,
                          scaler=None,
                          meta: dict = None) -> pd.DataFrame:
    """
    Build feature row matching training column order.
    Uses provided scaler + meta (from registry).
    """
    meta = meta or {}
    amount = t.amount
    avg = t.avg_amount_24h or amount

    row = {
        # PCA features (V1-V28) — 0 by default (simulation)
        'V1': 0, 'V2': 0, 'V3': 0, 'V4': 0, 'V5': 0, 'V6': 0, 'V7': 0,
        'V8': 0, 'V9': 0, 'V10': 0, 'V11': 0, 'V12': 0, 'V13': 0,
        'V14': 0, 'V15': 0, 'V16': 0, 'V17': 0, 'V18': 0, 'V19': 0,
        'V20': 0, 'V21': 0, 'V22': 0, 'V23': 0, 'V24': 0, 'V25': 0,
        'V26': 0, 'V27': 0, 'V28': 0,
        # Raw
        'Amount': amount,
        'Hour': t.hour,
        # Engineered
        'log_amount': np.log1p(amount),
        'is_night': 1 if t.hour in [0, 1, 2, 3, 4, 5] else 0,
        'is_business_hours': 1 if 9 <= t.hour <= 17 else 0,
        'txn_type': t.txn_type,
        'device_change': t.device_change,
        'location_change': t.location_change,
        'account_age_days': t.account_age_days,
        'is_new_account': 1 if t.account_age_days < 30 else 0,
        'txn_count_24h': t.txn_count_24h,
        'is_high_velocity': 1 if t.txn_count_24h > 10 else 0,
        'amount_vs_avg_ratio': amount / (avg + 1),
        'is_large_amount': 1 if amount > avg * 3 else 0,
        'is_small_amount': 1 if amount < 10 else 0,
        'night_plus_device_change':
            1 if (t.hour in [0, 1, 2, 3, 4, 5] and t.device_change) else 0,
        'new_account_plus_large':
            1 if (t.account_age_days < 30 and amount > avg * 3) else 0,
        'location_and_device_change': t.device_change + t.location_change,
    }

    # Use trained feature column order if available
    feature_cols = meta.get('feature_columns', list(row.keys()))
    df = pd.DataFrame([row])

    # Add missing columns as 0
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    df = df[feature_cols]

    # Scale Amount + Hour with loaded scaler
    if scaler is not None:
        try:
            df[['Amount', 'Hour']] = scaler.transform(df[['Amount', 'Hour']])
        except Exception:
            # If scaler fails (feature mismatch), skip scaling silently
            pass

    return df


# ============================================================
# RISK LEVEL HELPER
# ============================================================
def _risk_level(score: float, threshold: float) -> str:
    if score >= 0.8:
        return "HIGH"
    if score >= threshold:
        return "MEDIUM"
    if score >= 0.3:
        return "LOW"
    return "SAFE"


# ============================================================
# ENDPOINT 1: POST /fraud/predict
# ============================================================
@router.post("/predict")
def predict_fraud(t: TxnFeatures):
    """
    Fast prediction without SHAP explanation.
    Auto-reloads model if a new version has been activated.
    """
    model, scaler, threshold, meta = get_current()

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Fraud model not loaded. Run training/train_fraud.py first."
        )

    try:
        X = build_feature_vector(t, scaler, meta)
        proba = float(model.predict_proba(X)[0, 1])
        is_fraud = proba >= threshold

        # Top feature importance (from model — not SHAP)
        top_features = []
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                cols = X.columns.tolist()
                pairs = sorted(
                    zip(cols, importances),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                top_features = [
                    {'feature': k, 'importance': round(float(v), 4)}
                    for k, v in pairs
                ]
        except Exception:
            pass

        return {
            'fraud_score': round(proba, 4),
            'is_fraud': bool(is_fraud),
            'threshold': round(float(threshold), 4),
            'risk_level': _risk_level(proba, threshold),
            'top_features': top_features,
            'model': meta.get('best_model', 'XGBoost'),
            'model_version': registry.version_tag or 'unknown',
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


# ============================================================
# ENDPOINT 2: POST /fraud/explain  (SHAP)
# ============================================================
@router.post("/explain")
def explain_prediction(t: TxnFeatures):
    """
    Return prediction + SHAP feature contributions.
    Same input as /predict, but includes feature-level explanation.
    """
    model, scaler, threshold, meta = get_current()

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not trained yet."
        )

    try:
        X = build_feature_vector(t, scaler, meta)
        proba = float(model.predict_proba(X)[0, 1])
        is_fraud = proba >= threshold

        # SHAP explanation
        try:
            explanation = shap_service.explain(X, top_k=10)
        except Exception as e:
            explanation = {'error': f'SHAP failed: {str(e)}'}

        return {
            'prediction': {
                'fraud_score': round(proba, 4),
                'is_fraud': bool(is_fraud),
                'threshold': round(float(threshold), 4),
                'risk_level': _risk_level(proba, threshold),
            },
            'explanation': explanation,
            'model': meta.get('best_model', 'XGBoost'),
            'model_version': registry.version_tag or 'unknown',
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Explain error: {str(e)}"
        )


# ============================================================
# ENDPOINT 3: GET /fraud/model-info
# ============================================================
@router.get("/model-info")
def model_info():
    """Return current model metadata + version tag."""
    registry.check_reload()

    if not registry.is_loaded:
        return {'status': 'not_loaded'}

    return {
        'status': 'ready',
        'version_tag': registry.version_tag,
        'best_model': registry.meta.get('best_model'),
        'threshold': registry.threshold,
        'metrics': registry.meta.get('metrics', {}),
        'all_results': registry.meta.get('all_results', {}),
        'feature_count': len(registry.meta.get('feature_columns', [])),
    }


# ============================================================
# ENDPOINT 4: GET /fraud/shap-importance
# ============================================================
@router.get("/shap-importance")
def global_shap_importance():
    """Return global feature importance from SHAP analysis."""
    path = os.path.join(MODEL_DIR, 'shap_importance.json')
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail=(
                "Run training/explainability.py first to generate "
                "shap_importance.json"
            )
        )
    with open(path) as f:
        return json.load(f)