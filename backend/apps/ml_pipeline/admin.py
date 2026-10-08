from django.contrib import admin
from .models import ModelVersion, RetrainingJob, ModelPerformanceLog, DataDriftMetric


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = ['version_tag', 'model_type', 'status', 'auprc',
                    'roc_auc', 'recall', 'precision', 'created_at']
    list_filter = ['status', 'model_type']
    readonly_fields = ['created_at']


@admin.register(RetrainingJob)
class RetrainingJobAdmin(admin.ModelAdmin):
    list_display = ['job_id', 'trigger', 'status', 'started_at',
                    'completed_at', 'duration_sec']
    list_filter = ['status', 'trigger']
    readonly_fields = ['created_at']


@admin.register(DataDriftMetric)
class DataDriftMetricAdmin(admin.ModelAdmin):
    list_display = ['date', 'feature_name', 'psi_score', 'is_drifted']
    list_filter = ['is_drifted', 'feature_name']