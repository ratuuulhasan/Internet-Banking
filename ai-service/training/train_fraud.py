"""
Fraud Detection Model Training
Uses Kaggle Credit Card Fraud Detection dataset.

Steps:
1. Load & explore data
2. Handle class imbalance with SMOTE
3. Train XGBoost + Random Forest + Isolation Forest
4. Evaluate with ROC-AUC, AUPRC, Precision, Recall
5. Save best model + scaler + threshold
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    average_precision_score, precision_recall_curve, f1_score,
    precision_score, recall_score,
)
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'dataset', 'creditcard.csv')
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)


def load_data():
    print("📥 Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"   Shape: {df.shape}")
    print(f"   Fraud cases: {df['Class'].sum()} ({df['Class'].mean()*100:.3f}%)")
    return df


def explore_data(df):
    print("\n📊 Exploratory Analysis:")
    print(f"   Total transactions: {len(df):,}")
    print(f"   Fraud: {df['Class'].sum():,}")
    print(f"   Legit: {(df['Class'] == 0).sum():,}")
    print(f"   Fraud median amount: ${df[df['Class']==1]['Amount'].median():.2f}")
    print(f"   Legit median amount: ${df[df['Class']==0]['Amount'].median():.2f}")

    # Class imbalance
    print(f"\n   Imbalance ratio: 1 fraud per {int((df['Class']==0).sum() / df['Class'].sum())} legit")


def preprocess(df):
    print("\n🔧 Preprocessing...")

    # Feature engineering on raw dataset
    df = df.copy()

    # Convert Time (seconds) to Hour of day
    df['Hour'] = (df['Time'] / 3600) % 24
    df = df.drop('Time', axis=1)

    # Scale Amount and Hour
    scaler = StandardScaler()
    df[['Amount', 'Hour']] = scaler.fit_transform(df[['Amount', 'Hour']])

    X = df.drop('Class', axis=1)
    y = df['Class']

    print(f"   Features: {X.shape[1]}")
    print(f"   Samples: {X.shape[0]}")

    return X, y, scaler


def train_models(X_train, y_train, X_test, y_test):
    print("\n🎓 Training models...")

    # Apply SMOTE only to training data
    print("   Applying SMOTE to balance training data...")
    smote = SMOTE(random_state=42, sampling_strategy=0.5)  # Not full 1:1, mild
    X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)
    print(f"   After SMOTE → Fraud: {y_train_bal.sum():,}, Legit: {(y_train_bal==0).sum():,}")

    results = {}
    models = {}

    # ---- 1. Logistic Regression (baseline) ----
    print("\n   [1/4] Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
    lr.fit(X_train_bal, y_train_bal)
    results['LogisticRegression'] = evaluate(lr, X_test, y_test, 'Logistic Regression')
    models['LogisticRegression'] = lr

    # ---- 2. Random Forest ----
    print("\n   [2/4] Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=15, n_jobs=-1,
        random_state=42, class_weight='balanced'
    )
    rf.fit(X_train_bal, y_train_bal)
    results['RandomForest'] = evaluate(rf, X_test, y_test, 'Random Forest')
    models['RandomForest'] = rf

    # ---- 3. XGBoost ----
    print("\n   [3/4] XGBoost...")
    scale_pos_weight = (y_train_bal == 0).sum() / (y_train_bal == 1).sum()
    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric='aucpr',
        random_state=42,
        tree_method='hist',
        n_jobs=-1,
    )
    xgb.fit(X_train_bal, y_train_bal)
    results['XGBoost'] = evaluate(xgb, X_test, y_test, 'XGBoost')
    models['XGBoost'] = xgb

    # ---- 4. Isolation Forest (unsupervised baseline) ----
    print("\n   [4/4] Isolation Forest (unsupervised)...")
    iso = IsolationForest(contamination=0.002, random_state=42, n_jobs=-1)
    iso.fit(X_train)  # trained only on normal-ish data
    # Convert to 0/1
    iso_pred = (iso.predict(X_test) == -1).astype(int)
    iso_scores = -iso.decision_function(X_test)  # higher = more anomalous
    results['IsolationForest'] = {
        'roc_auc': roc_auc_score(y_test, iso_scores),
        'auprc': average_precision_score(y_test, iso_scores),
        'precision': precision_score(y_test, iso_pred, zero_division=0),
        'recall': recall_score(y_test, iso_pred, zero_division=0),
        'f1': f1_score(y_test, iso_pred, zero_division=0),
    }
    print(f"   IsolationForest → ROC-AUC: {results['IsolationForest']['roc_auc']:.4f} | AUPRC: {results['IsolationForest']['auprc']:.4f}")

    return models, results


def evaluate(model, X_test, y_test, name):
    """Evaluate a supervised model."""
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    roc = roc_auc_score(y_test, y_pred_proba)
    auprc = average_precision_score(y_test, y_pred_proba)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print(f"   {name} → ROC-AUC: {roc:.4f} | AUPRC: {auprc:.4f} | "
          f"P: {prec:.4f} | R: {rec:.4f} | F1: {f1:.4f}")

    return {
        'roc_auc': roc, 'auprc': auprc,
        'precision': prec, 'recall': rec, 'f1': f1,
    }


def find_optimal_threshold(model, X_test, y_test):
    """Find threshold that maximizes F1."""
    y_proba = model.predict_proba(X_test)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
    best_idx = np.argmax(f1_scores)
    best_threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
    print(f"\n🎯 Optimal threshold: {best_threshold:.4f} (F1={f1_scores[best_idx]:.4f})")
    return float(best_threshold)


def plot_results(results, model, X_test, y_test):
    """Generate plots."""
    try:
        # Comparison bar chart
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        models_list = list(results.keys())
        metrics = ['roc_auc', 'auprc', 'precision', 'recall', 'f1']
        x = np.arange(len(models_list))
        width = 0.15

        for i, m in enumerate(metrics):
            vals = [results[mod].get(m, 0) for mod in models_list]
            axes[0].bar(x + i * width, vals, width, label=m)
        axes[0].set_xticks(x + width * 2)
        axes[0].set_xticklabels(models_list, rotation=15)
        axes[0].set_title('Model Comparison')
        axes[0].legend()
        axes[0].set_ylim(0, 1.05)

        # Confusion matrix for best model
        y_pred = (model.predict_proba(X_test)[:, 1] >= 0.5).astype(int)
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[1])
        axes[1].set_title('Confusion Matrix (Best Model)')
        axes[1].set_xlabel('Predicted')
        axes[1].set_ylabel('Actual')

        plt.tight_layout()
        plot_path = os.path.join(MODEL_DIR, 'model_comparison.png')
        plt.savefig(plot_path, dpi=100)
        print(f"\n📈 Plot saved: {plot_path}")
    except Exception as e:
        print(f"   Plot skipped: {e}")


def main():
    print("=" * 60)
    print("🚀 FRAUD DETECTION MODEL TRAINING")
    print("=" * 60)

    # Load
    df = load_data()
    explore_data(df)

    # Preprocess
    X, y, scaler = preprocess(df)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"\n📊 Train: {len(X_train):,} | Test: {len(X_test):,}")

    # Train
    models, results = train_models(X_train, y_train, X_test, y_test)

    # Pick best (by AUPRC — best metric for imbalanced)
    best_name = max(results, key=lambda k: results[k].get('auprc', 0))
    best_model = models[best_name]
    print(f"\n🏆 Best model: {best_name}")
    print(f"   AUPRC: {results[best_name]['auprc']:.4f}")
    print(f"   ROC-AUC: {results[best_name]['roc_auc']:.4f}")

    # Optimal threshold
    threshold = find_optimal_threshold(best_model, X_test, y_test)

    # Save
    print("\n💾 Saving artifacts...")
    joblib.dump(best_model, os.path.join(MODEL_DIR, 'fraud_model.pkl'))
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'scaler.pkl'))
    joblib.dump(threshold, os.path.join(MODEL_DIR, 'threshold.pkl'))

    meta = {
        'best_model': best_name,
        'feature_columns': list(X.columns),
        'threshold': threshold,
        'metrics': results[best_name],
        'all_results': results,
    }
    with open(os.path.join(MODEL_DIR, 'model_meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"   ✅ fraud_model.pkl")
    print(f"   ✅ scaler.pkl")
    print(f"   ✅ threshold.pkl")
    print(f"   ✅ model_meta.json")

    # Plot
    plot_results(results, best_model, X_test, y_test)

    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()