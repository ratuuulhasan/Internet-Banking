"""
SHAP Explainability Service — CORRECTED VERSION
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
import shap

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'models')
EXPLAINER_PATH = os.path.join(MODEL_DIR, 'shap_explainer.pkl')


class ShapService:
    _instance = None
    _explainer = None
    _model = None
    _meta = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self):
        if self._explainer is not None:
            return self._explainer

        try:
            self._model = joblib.load(os.path.join(MODEL_DIR, 'fraud_model.pkl'))
            with open(os.path.join(MODEL_DIR, 'model_meta.json')) as f:
                self._meta = json.load(f)

            if os.path.exists(EXPLAINER_PATH):
                self._explainer = joblib.load(EXPLAINER_PATH)
                print("✅ SHAP explainer loaded from cache")
            else:
                print("⏳ Building SHAP explainer (first time)...")
                self._explainer = shap.TreeExplainer(self._model)
                joblib.dump(self._explainer, EXPLAINER_PATH)
                print("✅ SHAP explainer built and cached")

            return self._explainer
        except Exception as e:
            print(f"⚠️  SHAP service failed: {e}")
            return None

    def explain(self, X: pd.DataFrame, top_k: int = 8) -> dict:
        explainer = self.load()
        if explainer is None:
            return {'error': 'SHAP explainer unavailable'}

        shap_values = explainer.shap_values(X)

        # Handle different shap output formats
        if isinstance(shap_values, list):
            shap_vals = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            shap_vals = shap_values

        if shap_vals.ndim == 2:
            shap_vals = shap_vals[0]

        # ✅ FIX: Handle base_value properly
        base_value = explainer.expected_value
        if isinstance(base_value, (list, np.ndarray)):
            base_value = float(base_value[1] if len(base_value) > 1 else base_value[0])
        else:
            base_value = float(base_value)

        prediction = float(self._model.predict_proba(X)[0, 1])

        feature_names = X.columns.tolist()
        feature_values = X.iloc[0].tolist()

        pairs = list(zip(feature_names, feature_values, shap_vals))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)

        top_features = [
            {
                'feature': name,
                'shap_value': round(float(sv), 4),
                'feature_value': round(float(fv), 4),
                'direction': 'increases_risk' if sv > 0 else 'decreases_risk',
            }
            for name, fv, sv in pairs[:top_k]
        ]

        top_positive = [f for f in top_features if f['shap_value'] > 0][:5]
        top_negative = [f for f in top_features if f['shap_value'] < 0][:5]

        all_shap = {name: round(float(sv), 4) for name, _, sv in pairs}

        return {
            'base_value': round(base_value, 4),
            'prediction': round(prediction, 4),
            'top_features': top_features,
            'top_positive': top_positive,
            'top_negative': top_negative,
            'all_shap': all_shap,
        }


shap_service = ShapService()