from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import ModelVersion, RetrainingJob, ModelPerformanceLog, DataDriftMetric
from .serializers import (
    ModelVersionSerializer, RetrainingJobSerializer,
    PerformanceLogSerializer, DriftMetricSerializer,
)
from .tasks import retrain_fraud_model
from .utils import activate_version
from apps.users.permissions import IsAdmin
from apps.audit.utils import log_action


class ModelVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ModelVersion.objects.all()
    serializer_class = ModelVersionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Manually activate a specific version (rollback or promote)."""
        mv = self.get_object()
        if mv.status == 'ACTIVE':
            return Response({'error': 'Already active'}, status=400)

        try:
            # Archive current active
            current = ModelVersion.objects.filter(status='ACTIVE').exclude(pk=pk).first()
            if current:
                current.status = 'ARCHIVED'
                current.replaced_at = timezone.now()
                current.save()

            # Activate target
            activate_version(mv.version_tag)
            mv.status = 'ACTIVE'
            mv.activated_at = timezone.now()
            mv.save()

            log_action(request.user, 'MODEL_ACTIVATED', 'ModelVersion', mv.version_id)

            return Response({
                'message': f'{mv.version_tag} is now active',
                'version': ModelVersionSerializer(mv).data,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Return the active model."""
        mv = ModelVersion.objects.filter(status='ACTIVE').first()
        if not mv:
            return Response({'error': 'No active model'}, status=404)
        return Response(ModelVersionSerializer(mv).data)


class RetrainingJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RetrainingJob.objects.all()
    serializer_class = RetrainingJobSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """Manually trigger a retraining."""
        # Prevent concurrent jobs
        running = RetrainingJob.objects.filter(
            status__in=['PENDING', 'RUNNING']
        ).exists()
        if running:
            return Response(
                {'error': 'Another retraining job is already running'},
                status=400,
            )

        task = retrain_fraud_model.delay(
            trigger='MANUAL',
            user_id=request.user.user_id,
        )

        log_action(request.user, 'RETRAIN_TRIGGERED', 'MLPipeline')

        return Response({
            'message': 'Retraining started',
            'task_id': task.id,
        }, status=status.HTTP_202_ACCEPTED)


class MLDashboardStatsView(APIView):
    """Overview stats for ML dashboard."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        active = ModelVersion.objects.filter(status='ACTIVE').first()
        latest = ModelVersion.objects.first()
        running = RetrainingJob.objects.filter(status='RUNNING').first()

        return Response({
            'active_version': ModelVersionSerializer(active).data if active else None,
            'latest_version': ModelVersionSerializer(latest).data if latest else None,
            'running_job': RetrainingJobSerializer(running).data if running else None,
            'total_versions': ModelVersion.objects.count(),
            'total_jobs': RetrainingJob.objects.count(),
            'last_retrain': ModelVersion.objects.order_by('-created_at')
                            .values_list('created_at', flat=True).first(),
            'recent_drift': DriftMetricSerializer(
                DataDriftMetric.objects.all()[:5], many=True
            ).data,
        })


class PerformanceLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PerformanceLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        qs = ModelPerformanceLog.objects.all()
        version_id = self.request.query_params.get('version')
        if version_id:
            qs = qs.filter(model_version_id=version_id)
        return qs


class DriftMetricViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DataDriftMetric.objects.all()
    serializer_class = DriftMetricSerializer
    permission_classes = [IsAuthenticated, IsAdmin]