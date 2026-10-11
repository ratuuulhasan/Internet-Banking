from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import KYC
from .serializers import (
    KYCSerializer, KYCApprovalSerializer, KYCSubmitSerializer,
)
from .tasks import process_kyc_ocr
from apps.users.permissions import IsAdmin
from apps.audit.utils import log_action


class KYCViewSet(viewsets.ModelViewSet):
    serializer_class = KYCSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'EMPLOYEE']:
            return KYC.objects.all()
        return KYC.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        """
        KYC submission — creates record and triggers async OCR.
        """
        # Prevent duplicate KYC
        existing = KYC.objects.filter(user=request.user).first()
        if existing:
            if existing.status == 'APPROVED':
                return Response(
                    {'error': 'KYC already approved'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Allow re-submit if not approved
            serializer = self.get_serializer(existing, data=request.data, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        kyc = serializer.save(user=request.user)

        # Trigger async OCR
        task = process_kyc_ocr.delay(kyc.kyc_id)

        log_action(request.user, 'KYC_SUBMITTED', 'KYC', kyc.kyc_id,
                   {'task_id': task.id})

        return Response({
            'message': 'KYC submitted. OCR processing started.',
            'kyc_id': kyc.kyc_id,
            'task_id': task.id,
            'status': kyc.status,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reprocess_ocr(self, request, pk=None):
        """Re-run OCR on the KYC documents."""
        kyc = self.get_object()
        if kyc.user != request.user and request.user.role not in ['ADMIN', 'SYS_ADMIN']:
            return Response({'error': 'Permission denied'}, status=403)

        task = process_kyc_ocr.delay(kyc.kyc_id)
        return Response({
            'message': 'OCR reprocessing started',
            'task_id': task.id,
        })

    @action(detail=True, methods=['get'])
    def ocr_status(self, request, pk=None):
        """Poll OCR processing status."""
        kyc = self.get_object()
        return Response({
            'kyc_id': kyc.kyc_id,
            'status': kyc.status,
            'ocr_done': kyc.has_ocr_data,
            'fields_extracted': kyc.ocr_fields_extracted,
            'ocr_error': kyc.ocr_error,
        })

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsAdmin])
    def approve(self, request, pk=None):
        """Admin approves or rejects KYC."""
        kyc = self.get_object()
        serializer = KYCApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        kyc.status = serializer.validated_data['status']
        kyc.remarks = serializer.validated_data.get('remarks', '')
        kyc.verified_by = request.user
        kyc.verified_at = timezone.now()
        kyc.save()

        if kyc.status == 'APPROVED':
            kyc.user.status = 'ACTIVE'
            kyc.user.save()

        log_action(request.user, f'KYC_{kyc.status}', 'KYC', kyc.kyc_id)

        return Response(KYCSerializer(kyc).data)