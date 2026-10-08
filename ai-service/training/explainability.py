"""
Global SHAP analysis on the entire test set.
Generates summary, bar, and dependence plots.
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shap

from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models')
PLOTS_DIR = os.path.join(MODEL_DIR, 'shap_plots')
os.makedirs(PLOTS_DIR, exist_ok=True)

DATA_PATH = os.path.join(BASE_DIR, 'dataset', 'creditcard.csv')


def load_test_data(max_samples=1000):
    """Load small sample of test data for SHAP analysis."""
    print("📥 Loading data...")
    df = pd.read_csv(DATA_PATH)
    df['Hour'] = (df['Time'] / 3600) % 24
    df = df.drop('Time', axis=1)

    scaler = joblib.load(os.path.join(MODEL_DIR, 'scaler.pkl'))
    df[['Amount', 'Hour']] = scaler.transform(df[['Amount', 'Hour']])

    X = df.drop('Class', axis=1)
    y = df['Class']

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Take sample — include all frauds + random legit
    fraud_idx = y_test[y_test == 1].index
    legit_idx = y_test[y_test == 0].sample(
        n=min(max_samples - len(fraud_idx), 950), random_state=42
    ).index

    sample_idx = fraud_idx.union(legit_idx)
    print(f"   Sample size: {len(sample_idx)} (fraud: {len(fraud_idx)})")

    return X_test.loc[sample_idx], y_test.loc[sample_idx]


def main():
    print("=" * 60)
    print("🔍 SHAP EXPLAINABILITY ANALYSIS")
    print("=" * 60)

    # Load model
    print("\n📦 Loading model...")
    model = joblib.load(os.path.join(MODEL_DIR, 'fraud_model.pkl'))

    # Load data
    X_sample, y_sample = load_test_data(max_samples=1000)

    # Build SHAP explainer
    print("\n⏳ Building SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    joblib.dump(explainer, os.path.join(MODEL_DIR, 'shap_explainer.pkl'))
    print("✅ Explainer cached")

    # Compute SHAP values
    print("\n🔢 Computing SHAP values...")
    shap_values = explainer.shap_values(X_sample)
    if isinstance(shap_values, list):
        shap_vals = shap_values[1]  # fraud class
    else:
        shap_vals = shap_values
    print(f"   Shape: {shap_vals.shape}")

    # ---- 1. Summary plot (beeswarm) ----
    print("\n📊 Generating summary plot...")
    plt.figure(figsize=(11, 9))
    shap.summary_plot(shap_vals, X_sample, show=False, max_display=15)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'summary_plot.png'), dpi=120, bbox_inches='tight')
    plt.close()
    print("   ✅ summary_plot.png")

    # ---- 2. Bar plot (global importance) ----
    print("\n📊 Generating bar plot...")
    plt.figure(figsize=(11, 7))
    shap.summary_plot(shap_vals, X_sample, plot_type='bar', show=False, max_display=15)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'bar_plot.png'), dpi=120, bbox_inches='tight')
    plt.close()
    print("   ✅ bar_plot.png")

    # ---- 3. Dependence plots (top 3 features) ----
    print("\n📊 Generating dependence plots...")
    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    top_idx = np.argsort(mean_abs_shap)[::-1][:3]
    top_features = [X_sample.columns[i] for i in top_idx]
    print(f"   Top features: {top_features}")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for i, feat in enumerate(top_features):
        shap.dependence_plot(
            feat, shap_vals, X_sample,
            ax=axes[i], show=False
        )
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'dependence_plots.png'), dpi=120, bbox_inches='tight')
    plt.close()
    print("   ✅ dependence_plots.png")

    # ---- 4. Waterfall for a fraud sample ----
    print("\n📊 Generating waterfall plot (fraud sample)...")
    fraud_indices = y_sample[y_sample == 1].index
    if len(fraud_indices) > 0:
        fraud_pos = list(y_sample.index).index(fraud_indices[0])

        # Build Explanation object
        base = explainer.expected_value
        if isinstance(base, (list, np.ndarray)):
            base = base[1] if len(base) > 1 else base[0]

        explanation = shap.Explanation(
            values=shap_vals[fraud_pos],
            base_values=float(base),
            data=X_sample.iloc[fraud_pos].values,
            feature_names=X_sample.columns.tolist(),
        )

        plt.figure(figsize=(11, 7))
        shap.plots.waterfall(explanation, max_display=12, show=False)
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, 'waterfall_fraud.png'), dpi=120, bbox_inches='tight')
        plt.close()
        print("   ✅ waterfall_fraud.png")

    # ---- 5. Waterfall for legit sample ----
    print("\n📊 Generating waterfall plot (legit sample)...")
    legit_indices = y_sample[y_sample == 0].index
    if len(legit_indices) > 0:
        legit_pos = list(y_sample.index).index(legit_indices[0])
        base = explainer.expected_value
        if isinstance(base, (list, np.ndarray)):
            base = base[1] if len(base) > 1 else base[0]

        explanation = shap.Explanation(
            values=shap_vals[legit_pos],
            base_values=float(base),
            data=X_sample.iloc[legit_pos].values,
            feature_names=X_sample.columns.tolist(),
        )

        plt.figure(figsize=(11, 7))
        shap.plots.waterfall(explanation, max_display=12, show=False)
        plt.tight_layout()
        plt.savefig(os.path.join(PLOTS_DIR, 'waterfall_legit.png'), dpi=120, bbox_inches='tight')
        plt.close()
        print("   ✅ waterfall_legit.png")

    # ---- Save global feature importance JSON ----
    print("\n💾 Saving global importance...")
    importance = [
        {
            'feature': X_sample.columns[i],
            'mean_abs_shap': round(float(mean_abs_shap[i]), 5),
        }
        for i in np.argsort(mean_abs_shap)[::-1]
    ]
    with open(os.path.join(MODEL_DIR, 'shap_importance.json'), 'w') as f:
        json.dump(importance, f, indent=2)
    print("   ✅ shap_importance.json")

    print("\n" + "=" * 60)
    print(f"✅ SHAP ANALYSIS COMPLETE")
    print(f"   Plots saved in: {PLOTS_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()