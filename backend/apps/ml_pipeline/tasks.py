"""
Celery tasks for ML retraining pipeline.
"""
import time
import json
import traceback
from datetime import timedelta
from pathlib import Path

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import ModelVersion, RetrainingJob, DataDriftMetric, ModelPerformanceLog
from .utils import (
    generate_version_tag, run_training, validate_model,
    activate_version, cleanup_old_versions, compute_dataset_hash,
    get_ai_service_dir, get_registry_dir,
)


def _log(job: RetrainingJob, msg: str):
    """Append to job log."""
    job.log_output = (job.log_output or '') + f"\n[{timezone.now().isoformat()}] {msg}"
    job.save(update_fields=['log_output'])


@shared_task(bind=True, max_retries=1)
def retrain_fraud_model(self, trigger='MANUAL', user_id=None):
    """
    Main retraining task.
    Steps: train → validate → activate (or reject).
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Create job record
    job = RetrainingJob.objects.create(
        celery_task_id=self.request.id,
        trigger=trigger,
        status='RUNNING',
        started_at=timezone.now(),
        triggered_by=User.objects.filter(pk=user_id).first() if user_id else None,
    )

    start_time = time.time()
    _log(job, f"🚀 Retraining started (trigger={trigger})")

    try:
        # 1. Generate version tag
        version_tag = generate_version_tag()
        _log(job, f"📌 Version tag: {version_tag}")

        # 2. Create ModelVersion record
        mv = ModelVersion.objects.create(
            version_tag=version_tag,
            status='TRAINING',
            created_by=job.triggered_by,
        )

        # 3. Compute dataset hash
        ai_dir = get_ai_service_dir()
        dataset = ai_dir / 'training' / 'dataset' / 'creditcard.csv'
        dataset_hash = compute_dataset_hash(dataset)
        mv.dataset_hash = dataset_hash
        mv.save()

        # 4. Train model
        _log(job, "🎓 Training model...")
        train_start = time.time()
        result = run_training(version_tag)
        train_duration = time.time() - train_start
        _log(job, f"✅ Training done in {train_duration:.1f}s")

        # Update model version with training result
        metrics = result['metrics']
        mv.model_type = result['best_model']
        mv.roc_auc = metrics.get('roc_auc')
        mv.auprc = metrics.get('auprc')
        mv.precision = metrics.get('precision')
        mv.recall = metrics.get('recall')
        mv.f1_score = metrics.get('f1')
        mv.threshold = result['threshold']
        mv.training_duration_sec = train_duration
        mv.model_path = result['output_dir']
        mv.training_log = result['log']
        mv.status = 'CANDIDATE'
        mv.save()

        _log(job, f"📊 Metrics: AUPRC={mv.auprc:.4f}, ROC-AUC={mv.roc_auc:.4f}, "
                  f"P={mv.precision:.4f}, R={mv.recall:.4f}")

        # 5. Validate against baseline
        active = ModelVersion.objects.filter(status='ACTIVE').first()
        baseline_metrics = None
        if active:
            baseline_metrics = {
                'roc_auc': active.roc_auc,
                'auprc': active.auprc,
                'precision': active.precision,
                'recall': active.recall,
            }
            _log(job, f"🔍 Comparing against active {active.version_tag}")

        validation = validate_model({'metrics': metrics}, baseline_metrics)

        if not validation['valid']:
            mv.status = 'FAILED'
            mv.error_message = "Validation failed: " + " | ".join(validation['reasons'])
            mv.save()
            _log(job, f"❌ Validation failed: {validation['reasons']}")
            job.status = 'FAILED'
            job.error_message = "Validation failed"
            job.model_version = mv
            job.completed_at = timezone.now()
            job.duration_sec = time.time() - start_time
            job.save()
            return {'status': 'failed', 'reason': 'validation', 'version': version_tag}

        mv.status = 'VALIDATED'
        mv.save()
        _log(job, "✅ Validation passed")

        # 6. Auto-activate if configured
        if settings.ML_PIPELINE['AUTO_ACTIVATE']:
            _log(job, "🔄 Auto-activating new model...")

            # Archive current active
            if active:
                active.status = 'ARCHIVED'
                active.replaced_at = timezone.now()
                active.save()

            # Activate new
            activate_version(version_tag)
            mv.status = 'ACTIVE'
            mv.activated_at = timezone.now()
            mv.save()

            _log(job, f"🎯 {version_tag} is now ACTIVE")

        job.status = 'SUCCESS'
        job.model_version = mv
        job.completed_at = timezone.now()
        job.duration_sec = time.time() - start_time
        job.save()
        _log(job, f"✅ Pipeline complete ({job.duration_sec:.1f}s)")

        return {
            'status': 'success',
            'version': version_tag,
            'metrics': metrics,
            'activated': settings.ML_PIPELINE['AUTO_ACTIVATE'],
        }

    except Exception as e:
        tb = traceback.format_exc()
        _log(job, f"❌ Error: {e}\n{tb}")
        job.status = 'FAILED'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.duration_sec = time.time() - start_time
        job.save()
        raise


@shared_task
def scheduled_retrain_fraud():
    """Weekly scheduled retraining."""
    return retrain_fraud_model(trigger='SCHEDULED')


@shared_task
def validate_active_model():
    """
    Daily validation of the active model.
    Checks:
    1. AI service is healthy
    2. Model responds correctly
    3. Recent performance
    """
    from .models import ModelVersion
    active = ModelVersion.objects.filter(status='ACTIVE').first()
    if not active:
        return {'status': 'no_active_model'}

    try:
        r = requests.get(
            f"{settings.AI_SERVICE_URL}/fraud/model-info",
            timeout=5,
        )
        if r.status_code != 200:
            return {'status': 'unhealthy', 'code': r.status_code}

        info = r.json()

        # Log daily performance
        today = timezone.now().date()
        perf, _ = ModelPerformanceLog.objects.get_or_create(
            model_version=active,
            date=today,
        )

        return {
            'status': 'healthy',
            'active_version': active.version_tag,
            'ai_info': info,
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


@shared_task
def cleanup_old_versions():
    """Monthly cleanup of old model files."""
    keep = settings.ML_PIPELINE.get('KEEP_LAST_VERSIONS', 10)
    cleanup_old_versions(keep)
    return {'status': 'done', 'kept': keep}


@shared_task
def check_ai_service_health():
    """Periodic health check."""
    try:
        r = requests.get(f"{settings.AI_SERVICE_URL}/health", timeout=3)
        return {
            'status': 'ok' if r.status_code == 200 else 'unhealthy',
            'code': r.status_code,
            'body': r.json() if r.status_code == 200 else None,
        }
    except Exception as e:
        return {'status': 'unreachable', 'error': str(e)}


@shared_task
def detect_data_drift():
    """
    Detect feature drift by comparing recent transaction features
    against baseline (training distribution).
    Uses PSI (Population Stability Index).
    """
    from apps.transactions.models import Transaction
    from datetime import timedelta

    # Recent vs baseline
    recent = Transaction.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    )
    baseline = Transaction.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=30)
    )

    if recent.count() < 50 or baseline.count() < 50:
        return {'status': 'insufficient_data'}

    # Calculate PSI for amount
    import numpy as np

    def psi(expected, actual, buckets=10):
        """Population Stability Index."""
        breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
        breakpoints[0] = -np.inf
        breakpoints[-1] = np.inf

        expected_perc = np.histogram(expected, breakpoints)[0] / len(expected)
        actual_perc = np.histogram(actual, breakpoints)[0] / len(actual)

        # Avoid div by zero
        expected_perc = np.where(expected_perc == 0, 0.0001, expected_perc)
        actual_perc = np.where(actual_perc == 0, 0.0001, actual_perc)

        return np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc))

    baseline_amounts = np.array([float(t.amount) for t in baseline])
    recent_amounts = np.array([float(t.amount) for t in recent])

    amount_psi = psi(baseline_amounts, recent_amounts)
    is_drifted = amount_psi > 0.25   # PSI > 0.25 = significant drift

    DataDriftMetric.objects.create(
        feature_name='amount',
        psi_score=float(amount_psi),
        is_drifted=is_drifted,
        baseline_mean=float(baseline_amounts.mean()),
        current_mean=float(recent_amounts.mean()),
    )

    # Auto-trigger retraining if severe drift
    if amount_psi > 0.5:
        retrain_fraud_model.delay(trigger='DRIFT')

    return {
        'status': 'done',
        'psi': float(amount_psi),
        'is_drifted': is_drifted,
        'retrained': amount_psi > 0.5,
    }