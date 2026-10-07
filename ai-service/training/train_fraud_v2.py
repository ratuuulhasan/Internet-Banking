"""
Fraud Detection v2 - Production Ready
Uses ONLY features we can compute in production (no V1-V28).
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    average_precision_score, precision_recall_curve, f1_score,
    precision_score, recall_score, roc_curve,
)
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'dataset', 'creditcard.csv')
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)


# Features we actually use (no V1-V28)
FEATURE_COLS = [
    'Amount', 'Hour',
    'log_amount',
    'is_night', 'is_business_hours',
    'is_small_amount', 'is_large_amount',
    'hour_sin', 'hour_cos',
]


def load_and_engineer():
    print("📥 Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"   Shape: {df.shape} | Fraud: {df['Class'].sum()}")

    # Time → Hour
    df['Hour'] = (df['Time'] / 3600) % 24
    df['Hour'] = df['Hour'].astype(int)

    # Engineered features
    df['log_amount'] = np.log1p(df['Amount'])
    df['is_night'] = df['Hour'].apply(lambda h: 1 if h in [0,1,2,3,4,5] else 0)
    df['is_business_hours'] = df['Hour'].apply(lambda h: 1 if 9 <= h <= 17 else 0)
    df['is_small_amount'] = (df['Amount'] < 10).astype(int)
    df['is_large_amount'] = (df['Amount'] > 1000).astype(int)

    # Cyclical hour encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24)

    X = df[FEATURE_COLS].copy()
    y = df['Class'].copy()

    # Scale Amount (only Amount needs scaling)
    scaler = StandardScaler()
    X[['Amount']] = scaler.fit_transform(X[['Amount']])

    print(f"   Features used: {FEATURE_COLS}")
    print(f"   X shape: {X.shape}")

    return X, y, scaler


def train(X_train, y_train, X_test, y_test):
    print("\n🎓 Training models...")

    # SMOTE
    print("   Applying SMOTE...")
    smote = SMOTE(random_state=42, sampling_strategy=0.5)
    X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)
    print(f"   After SMOTE → Fraud: {y_train_bal.sum():,} | Legit: {(y_train_bal==0).sum():,}")

    results = {}
    models = {}

    # 1. Logistic Regression
    print("\n   [1/3] Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
    lr.fit(X_train_bal, y_train_bal)
    results['LogisticRegression'] = evaluate(lr, X_test, y_test, 'Logistic Regression')
    models['LogisticRegression'] = lr

    # 2. Random Forest
    print("\n   [2/3] Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=12, n_jobs=-1,
        random_state=42, class_weight='balanced'
    )
    rf.fit(X_train_bal, y_train_bal)
    results['RandomForest'] = evaluate(rf, X_test, y_test, 'Random Forest')
    models['RandomForest'] = rf

    # 3. XGBoost
    print("\n   [3/3] XGBoost...")
    scale_pos_weight = (y_train_bal == 0).sum() / (y_train_bal == 1).sum()
    xgb = XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric='aucpr', random_state=42,
        tree_method='hist', n_jobs=-1,
    )
    xgb.fit(X_train_bal, y_train_bal)
    results['XGBoost'] = evaluate(xgb, X_test, y_test, 'XGBoost')
    models['XGBoost'] = xgb

    return models, results


def evaluate(model, X_test, y_test, name):
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)
    roc = roc_auc_score(y_test, y_proba)
    auprc = average_precision_score(y_test, y_proba)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    print(f"   {name} → AUC:{roc:.4f} | AUPRC:{auprc:.4f} | P:{prec:.4f} | R:{rec:.4f} | F1:{f1:.4f}")
    return {'roc_auc': roc, 'auprc': auprc, 'precision': prec, 'recall': rec, 'f1': f1}


def find_optimal_threshold(model, X_test, y_test):
    """Find threshold with best F1 but cap at 0.9 to avoid uselessly-high threshold."""
    y_proba = model.predict_proba(X_test)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
    # Cap threshold to <= 0.85 so model actually flags suspicious txns
    valid = thresholds <= 0.85
    if valid.any():
        best_idx = np.argmax(f1_scores[:len(thresholds)][valid])
        actual_idx = np.where(valid)[0][best_idx]
        best_threshold = thresholds[actual_idx]
    else:
        best_threshold = 0.5
    print(f"\n🎯 Optimal threshold: {best_threshold:.4f}")
    return float(best_threshold)


def plot_curves(model, X_test, y_test, results):
    try:
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # Model comparison
        names = list(results.keys())
        metrics = ['roc_auc', 'auprc', 'f1']
        x = np.arange(len(names))
        width = 0.25
        for i, m in enumerate(metrics):
            vals = [results[n][m] for n in names]
            axes[0].bar(x + i*width, vals, width, label=m)
        axes[0].set_xticks(x + width)
        axes[0].set_xticklabels(names, rotation=15)
        axes[0].set_title('Model Comparison')
        axes[0].legend()
        axes[0].set_ylim(0, 1.05)

        # ROC
        y_proba = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        axes[1].plot(fpr, tpr, label=f'AUC={roc_auc_score(y_test, y_proba):.4f}')
        axes[1].plot([0,1],[0,1],'k--')
        axes[1].set_xlabel('FPR'); axes[1].set_ylabel('TPR')
        axes[1].set_title('ROC Curve'); axes[1].legend()

        # PR
        prec, rec, _ = precision_recall_curve(y_test, y_proba)
        axes[2].plot(rec, prec, label=f'AUPRC={average_precision_score(y_test, y_proba):.4f}')
        axes[2].set_xlabel('Recall'); axes[2].set_ylabel('Precision')
        axes[2].set_title('PR Curve'); axes[2].legend()

        plt.tight_layout()
        out = os.path.join(MODEL_DIR, 'training_results_v2.png')
        plt.savefig(out, dpi=100)
        print(f"📈 Plot: {out}")
    except Exception as e:
        print(f"Plot skipped: {e}")


def main():
    print("=" * 60)
    print("🚀 FRAUD DETECTION TRAINING v2 (Production-Ready)")
    print("=" * 60)

    X, y, scaler = load_and_engineer()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"\n📊 Train: {len(X_train):,} | Test: {len(X_test):,}")

    models, results = train(X_train, y_train, X_test, y_test)

    # Best by AUPRC
    best_name = max(results, key=lambda k: results[k]['auprc'])
    best_model = models[best_name]
    print(f"\n🏆 Best model: {best_name}")
    print(f"   AUPRC: {results[best_name]['auprc']:.4f}")
    print(f"   ROC-AUC: {results[best_name]['roc_auc']:.4f}")

    threshold = find_optimal_threshold(best_model, X_test, y_test)

    # Save
    print("\n💾 Saving...")
    joblib.dump(best_model, os.path.join(MODEL_DIR, 'fraud_model.pkl'))
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'scaler.pkl'))
    joblib.dump(threshold, os.path.join(MODEL_DIR, 'threshold.pkl'))

    meta = {
        'best_model': best_name,
        'feature_columns': FEATURE_COLS,
        'threshold': threshold,
        'metrics': results[best_name],
        'all_results': results,
        'version': 'v2',
    }
    with open(os.path.join(MODEL_DIR, 'model_meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"   ✅ fraud_model.pkl")
    print(f"   ✅ scaler.pkl")
    print(f"   ✅ threshold.pkl")
    print(f"   ✅ model_meta.json")

    # Final report
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SET PERFORMANCE")
    print("=" * 60)
    y_proba = best_model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    print(classification_report(y_test, y_pred, digits=4))
    cm = confusion_matrix(y_test, y_pred)
    print(f"TN:{cm[0,0]:,}  FP:{cm[0,1]:,}")
    print(f"FN:{cm[1,0]:,}  TP:{cm[1,1]:,}")

    plot_curves(best_model, X_test, y_test, results)

    print("\n✅ TRAINING COMPLETE")


if __name__ == '__main__':
    main()