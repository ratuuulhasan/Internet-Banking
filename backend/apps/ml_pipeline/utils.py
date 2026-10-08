"""
Utilities for retraining pipeline.
Handles training, validation, model registry.
"""
import os
import json
import shutil
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.utils import timezone


def get_ai_service_dir() -> Path:
    """Return absolute path to ai-service directory."""
    base = Path(settings.BASE_DIR).parent
    ai_dir = Path(settings.ML_PIPELINE['AI_SERVICE_DIR'])
    if not ai_dir.is_absolute():
        ai_dir = base / ai_dir
    return ai_dir.resolve()


def get_registry_dir() -> Path:
    """Return path to model registry."""
    path = get_ai_service_dir() / 'models' / 'registry'
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_version_tag() -> str:
    """Generate unique version tag like v3_20260108_120000."""
    registry = get_registry_dir()
    existing = [d.name for d in registry.iterdir() if d.is_dir()]
    next_num = len(existing) + 1
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"v{next_num}_{timestamp}"


def compute_dataset_hash(dataset_path: Path) -> str:
    """Compute SHA256 of dataset for tracking."""
    if not dataset_path.exists():
        return ''
    h = hashlib.sha256()
    with open(dataset_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def run_training(version_tag: str) -> dict:
    """
    Execute training script and return metrics.
    Runs in ai-service venv if possible, else system python.
    """
    ai_dir = get_ai_service_dir()
    training_dir = ai_dir / 'training'

    # Output model goes to registry/<version_tag>/
    output_dir = get_registry_dir() / version_tag
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy training script path
    script = training_dir / 'train_fraud.py'
    if not script.exists():
        raise FileNotFoundError(f"Training script not found: {script}")

    # Set env vars for output
    env = os.environ.copy()
    env['MODEL_OUTPUT_DIR'] = str(output_dir)
    env['PYTHONUNBUFFERED'] = '1'

    # Run training
    result = subprocess.run(
        ['python', str(script)],
        cwd=str(training_dir),
        env=env,
        capture_output=True,
        text=True,
        timeout=3600,   # 1 hour
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Training failed (exit {result.returncode}):\n"
            f"{result.stderr[-2000:]}"
        )

    # Load metrics
    meta_path = output_dir / 'model_meta.json'
    if not meta_path.exists():
        # Fallback: check models dir
        meta_path = ai_dir / 'models' / 'model_meta.json'

    if not meta_path.exists():
        raise FileNotFoundError(f"Metrics not found at {meta_path}")

    with open(meta_path) as f:
        meta = json.load(f)

    return {
        'output_dir': str(output_dir),
        'metrics': meta.get('metrics', {}),
        'best_model': meta.get('best_model', 'XGBoost'),
        'threshold': meta.get('threshold', 0.5),
        'log': result.stdout[-5000:],
        'meta': meta,
    }


def validate_model(version_meta: dict, baseline_metrics: dict = None) -> dict:
    """
    Validate new model against minimum thresholds and baseline.

    Returns:
        {
            'valid': True/False,
            'reasons': ['...'],
            'metrics': {...},
        }
    """
    metrics = version_meta.get('metrics', {})
    min_cfg = settings.ML_PIPELINE

    reasons = []
    valid = True

    # Hard floors
    if metrics.get('recall', 0) < min_cfg['MIN_RECALL']:
        valid = False
        reasons.append(
            f"Recall {metrics.get('recall'):.4f} < {min_cfg['MIN_RECALL']}"
        )

    if metrics.get('precision', 0) < min_cfg['MIN_PRECISION']:
        valid = False
        reasons.append(
            f"Precision {metrics.get('precision'):.4f} < {min_cfg['MIN_PRECISION']}"
        )

    # Baseline comparison
    if baseline_metrics:
        old_auprc = baseline_metrics.get('auprc', 0)
        new_auprc = metrics.get('auprc', 0)
        improvement = new_auprc - old_auprc

        if improvement < min_cfg['MIN_AUPRC_IMPROVEMENT']:
            valid = False
            reasons.append(
                f"AUPRC improvement {improvement:+.4f} < "
                f"{min_cfg['MIN_AUPRC_IMPROVEMENT']} (old={old_auprc:.4f}, "
                f"new={new_auprc:.4f})"
            )

    return {
        'valid': valid,
        'reasons': reasons if reasons else ['All checks passed ✅'],
        'metrics': metrics,
    }


def activate_version(version_tag: str) -> bool:
    """
    Make a version the active model by updating pointer file.
    AI service reads current_version.txt on each request (or reloads).
    """
    ai_dir = get_ai_service_dir()
    registry = get_registry_dir()
    version_dir = registry / version_tag

    if not version_dir.exists():
        raise FileNotFoundError(f"Version dir not found: {version_dir}")

    # Write pointer
    pointer = ai_dir / 'models' / 'current_version.txt'
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(version_tag)

    # Copy artifacts to top-level models/ for AI service to pick up
    top_models = ai_dir / 'models'
    for fname in ['fraud_model.pkl', 'scaler.pkl', 'threshold.pkl', 'model_meta.json']:
        src = version_dir / fname
        if src.exists():
            shutil.copy2(src, top_models / fname)

    # Regenerate SHAP explainer
    try:
        _regenerate_shap(version_dir)
    except Exception as e:
        print(f"⚠️  SHAP regenerate failed: {e}")

    # Signal AI service to reload (via flag file)
    reload_flag = ai_dir / 'models' / 'reload.flag'
    reload_flag.write_text(str(timezone.now().timestamp()))

    return True


def _regenerate_shap(version_dir: Path):
    """Regenerate SHAP explainer for the new model."""
    ai_dir = get_ai_service_dir()
    subprocess.run(
        ['python', '-c', '''
import os, joblib, shap
from pathlib import Path
vd = Path(os.environ["VERSION_DIR"])
model = joblib.load(vd / "fraud_model.pkl")
explainer = shap.TreeExplainer(model)
joblib.dump(explainer, vd.parent.parent / "shap_explainer.pkl")
print("SHAP regenerated")
'''],
        cwd=str(ai_dir),
        env={**os.environ, 'VERSION_DIR': str(version_dir)},
        capture_output=True,
        text=True,
        timeout=300,
    )


def cleanup_old_versions(keep_last: int = 10):
    """Remove old registry folders beyond keep_last."""
    registry = get_registry_dir()
    dirs = sorted(
        [d for d in registry.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for old_dir in dirs[keep_last:]:
        shutil.rmtree(old_dir, ignore_errors=True)
        print(f"🗑️  Removed: {old_dir.name}")