from rest_framework import serializers
from .models import ModelVersion, RetrainingJob, ModelPerformanceLog, DataDriftMetric


class ModelVersionSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = ModelVersion
        fields = [
            'version_id', 'version_tag', 'model_type', 'status',
            'roc_auc', 'auprc', 'precision', 'recall', 'f1_score', 'threshold',
            'training_samples', 'fraud_samples', 'training_duration_sec',
            'dataset_hash', 'model_path',
            'created_at', 'activated_at', 'replaced_at',
            'created_by', 'created_by_email', 'error_message',
        ]
        read_only_fields = fields


class RetrainingJobSerializer(serializers.ModelSerializer):
    model_version_tag = serializers.CharField(
        source='model_version.version_tag', read_only=True
    )
    triggered_by_email = serializers.CharField(
        source='triggered_by.email', read_only=True
    )

    class Meta:
        model = RetrainingJob
        fields = [
            'job_id', 'celery_task_id', 'trigger', 'status',
            'model_version', 'model_version_tag',
            'started_at', 'completed_at', 'duration_sec',
            'triggered_by', 'triggered_by_email',
            'log_output', 'error_message', 'created_at',
        ]
        read_only_fields = fields


class PerformanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelPerformanceLog
        fields = '__all__'


class DriftMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDriftMetric
        fields = '__all__'