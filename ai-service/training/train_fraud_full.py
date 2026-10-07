"""
v1 Model — Full Kaggle Features (V1-V28 + Amount + Hour)
Saves as fraud_model_full.pkl (not overwriting v2)
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             precision_score, recall_score, f1_score,
                             precision_recall_curve)
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'dataset', 'creditcard.csv')
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models')


def main():
    print("📥 Loading Kaggle dataset...")
    df = pd.read_csv(DATA_PATH)

    # Time -> Hour
    df['Hour'] = ((df['Time'] / 3600) % 24).astype(int)
    df = df.drop('Time', axis=1)

    # Scale Amount + Hour
    scaler = StandardScaler()
    df[['Amount', 'Hour']] = scaler.fit_transform(df[['Amount', 'Hour']])

    X = df.drop('Class', axis=1)
    y = df['Class']

    feature_cols = list(X.columns)
    print(f"   Features ({len(feature_cols)}): {feature_cols[:5]}... + V1-V28")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    print("\n🎓 Applying SMOTE...")
    smote = SMOTE(random_state=42, sampling_strategy=0.5)
    X_tr, y_tr = smote.fit_resample(X_train, y_train)
    print(f"   Balanced → fraud:{y_tr.sum():,} legit:{(y_tr==0).sum():,}")

    print("\n🌲 Training XGBoost...")
    spw = (y_tr == 0).sum() / (y_tr == 1).sum()
    model = XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8,
        scale_pos_weight=spw, eval_metric='aucpr',
        random_state=42, tree_method='hist', n_jobs=-1,
    )
    model.fit(X_tr, y_tr)

    # Evaluate
    y_proba = model.predict_proba(X_test)[:, 1]
    roc = roc_auc_score(y_test, y_proba)
    auprc = average_precision_score(y_test, y_proba)
    print(f"\n📊 ROC-AUC: {roc:.4f} | AUPRC: {auprc:.4f}")

    # Optimal threshold (cap at 0.7 for usability)
    prec, rec, thr = precision_recall_curve(y_test, y_proba)
    f1s = 2 * prec * rec / (prec + rec + 1e-10)
    valid = thr <= 0.7
    idx = np.where(valid)[0][np.argmax(f1s[:len(thr)][valid])]
    best_thr = float(thr[idx]) if idx < len(thr) else 0.5
    print(f"🎯 Threshold: {best_thr:.4f}")

    # Save
    joblib.dump(model, os.path.join(MODEL_DIR, 'fraud_model_full.pkl'))
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'scaler_full.pkl'))
    joblib.dump(best_thr, os.path.join(MODEL_DIR, 'threshold_full.pkl'))

    with open(os.path.join(MODEL_DIR, 'meta_full.json'), 'w') as f:
        json.dump({
            'model': 'XGBoost-Full',
            'feature_columns': feature_cols,
            'threshold': best_thr,
            'roc_auc': roc, 'auprc': auprc,
        }, f, indent=2)

    print("\n✅ Saved: fraud_model_full.pkl + scaler_full.pkl + threshold_full.pkl")


if __name__ == '__main__':
    main()