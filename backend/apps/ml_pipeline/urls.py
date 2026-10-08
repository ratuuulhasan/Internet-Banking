from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ModelVersionViewSet, RetrainingJobViewSet,
    PerformanceLogViewSet, DriftMetricViewSet,
    MLDashboardStatsView,
)

router = DefaultRouter()
router.register('versions', ModelVersionViewSet, basename='model-versions')
router.register('jobs', RetrainingJobViewSet, basename='retraining-jobs')
router.register('performance', PerformanceLogViewSet, basename='performance')
router.register('drift', DriftMetricViewSet, basename='drift')

urlpatterns = [
    path('stats/', MLDashboardStatsView.as_view(), name='ml-stats'),
    path('', include(router.urls)),
]