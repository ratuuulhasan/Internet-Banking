from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import (
    AdminUserViewSet,
    AdminDashboardStatsView,
    AdminRecentActivityView,
    AdminFraudAlertsView,
)

router = DefaultRouter()
router.register('users', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    path('stats/', AdminDashboardStatsView.as_view(), name='admin-stats'),
    path('activity/', AdminRecentActivityView.as_view(), name='admin-activity'),
    path('fraud-alerts/', AdminFraudAlertsView.as_view(), name='admin-fraud-alerts'),
    path('', include(router.urls)),
]