from fastapi import APIRouter
from pydantic import BaseModel
import numpy as np
import os
from sklearn.ensemble import IsolationForest

router = APIRouter()

MODEL_PATH = "models/fraud_model.pkl"

class TxnFeatures(BaseModel):
    amount: float
    hour: int
    txn_type: int
    device_change: int = 0
    location_change: int = 0
    account_age_days: int = 0

# Load or train quick model
def load_model():
    import joblib
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    # Quick synthetic training if model not found
    np.random.seed(42)
    normal = np.random.randn(500, 6) * [1000, 5, 1, 0.1, 0.1, 100] + [5000, 12, 1, 0, 0, 365]
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(normal)
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return model

model = load_model()

@router.post("/predict")
def predict(t: TxnFeatures):
    X = np.array([[t.amount, t.hour, t.txn_type,
                   t.device_change, t.location_change, t.account_age_days]])
    pred = model.predict(X)[0]
    # Convert to 0-1 score
    score_raw = model.decision_function(X)[0]
    fraud_score = max(0.0, min(1.0, -score_raw))
    return {
        "fraud_score": round(float(fraud_score), 4),
        "is_fraud": bool(pred == -1),
    }