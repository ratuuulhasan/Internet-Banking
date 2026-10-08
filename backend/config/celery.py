import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('internet_banking')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# ============ PERIODIC SCHEDULE ============
app.conf.beat_schedule = {

    # Retrain fraud model — every Sunday 2 AM
    'retrain-fraud-weekly': {
        'task': 'apps.ml_pipeline.tasks.scheduled_retrain_fraud',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),   # Sunday 2:00
    },

    # Validate active model — daily at 3 AM
    'validate-active-model-daily': {
        'task': 'apps.ml_pipeline.tasks.validate_active_model',
        'schedule': crontab(hour=3, minute=0),
    },

    # Cleanup old model versions — monthly 1st at 4 AM
    'cleanup-old-models-monthly': {
        'task': 'apps.ml_pipeline.tasks.cleanup_old_versions',
        'schedule': crontab(hour=4, minute=0, day_of_month=1),
    },

    # Health check — every 30 minutes
    'ai-service-health': {
        'task': 'apps.ml_pipeline.tasks.check_ai_service_health',
        'schedule': crontab(minute='*/30'),
    },

    # Drift detection — daily 5 AM
    'detect-drift-daily': {
        'task': 'apps.ml_pipeline.tasks.detect_data_drift',
        'schedule': crontab(hour=5, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')