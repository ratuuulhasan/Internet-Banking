"""Standalone model evaluation."""
import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, average_precision_score,
    precision_recall_curve, roc_curve,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models')
DATA_PATH = os.path.join(BASE_DIR, 'dataset', 'creditcard.csv')


def main():
    print("🔍 Loading model and data...")
    model = joblib.load(os.path.join(MODEL_DIR, 'fraud_model.pkl'))
    scaler = joblib.load(os.path.join(MODEL_DIR, 'scaler.pkl'))
    threshold = joblib.load(os.path.join(MODEL_DIR, 'threshold.pkl'))

    with open(os.path.join(MODEL_DIR, 'model_meta.json')) as f:
        meta = json.load(f)

    feature_cols = meta.get('feature_columns', [])

    df = pd.read_csv(DATA_PATH)
    df['Hour'] = ((df['Time'] / 3600) % 24).astype(int)
    df['log_amount'] = np.log1p(df['Amount'])
    df['is_night'] = df['Hour'].apply(lambda h: 1 if h in [0,1,2,3,4,5] else 0)
    df['is_business_hours'] = df['Hour'].apply(lambda h: 1 if 9 <= h <= 17 else 0)
    df['is_small_amount'] = (df['Amount'] < 10).astype(int)
    df['is_large_amount'] = (df['Amount'] > 1000).astype(int)
    df['hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24)

    df[['Amount']] = scaler.transform(df[['Amount']])

    X = df[feature_cols]
    y = df['Class']

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)

    print("\n" + "=" * 60)
    print(f"📊 EVALUATION (threshold={threshold:.4f})")
    print("=" * 60)
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")
    print(f"AUPRC:   {average_precision_score(y_test, y_proba):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4))

    cm = confusion_matrix(y_test, y_pred)
    print(f"TN:{cm[0,0]:,}  FP:{cm[0,1]:,}")
    print(f"FN:{cm[1,0]:,}  TP:{cm[1,1]:,}")


if __name__ == '__main__':
    main()