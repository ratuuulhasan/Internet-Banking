from django.db import models
from django.conf import settings


class ModelVersion(models.Model):
    """Tracks each trained model version."""
    STATUS = [
        ('TRAINING', 'Training'),
        ('CANDIDATE', 'Candidate'),     # trained, waiting for evaluation
        ('VALIDATED', 'Validated'),     # passed validation, ready to activate
        ('ACTIVE', 'Active'),           # currently serving
        ('ARCHIVED', 'Archived'),       # replaced but kept
        ('FAILED', 'Failed'),           # training/validation failed
        ('ROLLED_BACK', 'Rolled Back'), # was active, reverted
    ]

    version_id = models.AutoField(primary_key=True)
    version_tag = models.CharField(max_length=100, unique=True)  # e.g. v3_20260108_120000
    model_type = models.CharField(max_length=50, default='XGBoost')

    # Metrics
    roc_auc = models.FloatField(null=True, blank=True)
    auprc = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    threshold = models.FloatField(null=True, blank=True)

    # Training info
    training_samples = models.IntegerField(null=True, blank=True)
    fraud_samples = models.IntegerField(null=True, blank=True)
    training_duration_sec = models.FloatField(null=True, blank=True)
    dataset_hash = models.CharField(max_length=64, blank=True)

    # Storage
    model_path = models.CharField(max_length=500, blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default='TRAINING')

    # Notes
    training_log = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    replaced_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trained_models'
    )

    class Meta:
        db_table = 'ml_model_versions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.version_tag} [{self.status}]"

    @property
    def is_active(self):
        return self.status == 'ACTIVE'


class RetrainingJob(models.Model):
    """Tracks each retraining run."""
    TRIGGERS = [
        ('MANUAL', 'Manual'),
        ('SCHEDULED', 'Scheduled'),
        ('DRIFT', 'Drift Detected'),
        ('DEGRADATION', 'Performance Drop'),
    ]
    STATUS = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    job_id = models.AutoField(primary_key=True)
    celery_task_id = models.CharField(max_length=100, blank=True)
    trigger = models.CharField(max_length=20, choices=TRIGGERS, default='MANUAL')
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')

    # Reference to trained model (if successful)
    model_version = models.ForeignKey(
        ModelVersion, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='retraining_jobs'
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_sec = models.FloatField(null=True, blank=True)

    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='triggered_jobs'
    )

    log_output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ml_retraining_jobs'
        ordering = ['-created_at']


class ModelPerformanceLog(models.Model):
    """Track performance metrics over time (from production predictions)."""
    log_id = models.AutoField(primary_key=True)
    model_version = models.ForeignKey(
        ModelVersion, on_delete=models.CASCADE,
        related_name='performance_logs'
    )
    date = models.DateField()
    predictions_count = models.IntegerField(default=0)
    flagged_count = models.IntegerField(default=0)
    confirmed_fraud = models.IntegerField(default=0)     # labeled by admin
    false_positive = models.IntegerField(default=0)
    avg_fraud_score = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'ml_performance_logs'
        unique_together = ('model_version', 'date')
        ordering = ['-date']


class DataDriftMetric(models.Model):
    """Stores drift detection results."""
    metric_id = models.AutoField(primary_key=True)
    date = models.DateField(auto_now_add=True)
    feature_name = models.CharField(max_length=100)
    psi_score = models.FloatField(help_text='Population Stability Index')
    is_drifted = models.BooleanField(default=False)
    baseline_mean = models.FloatField(null=True, blank=True)
    current_mean = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'ml_data_drift_metrics'
        ordering = ['-date']