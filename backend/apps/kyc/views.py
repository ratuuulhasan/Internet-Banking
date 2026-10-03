from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import KYC
from .serializers import KYCSerializer, KYCApprovalSerializer
from apps.users.permissions import IsAdmin


class KYCViewSet(viewsets.ModelViewSet):
    serializer_class = KYCSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'EMPLOYEE']:
            return KYC.objects.all()
        return KYC.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def approve(self, request, pk=None):
        kyc = self.get_object()
        serializer = KYCApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        kyc.status = serializer.validated_data['status']
        kyc.remarks = serializer.validated_data.get('remarks', '')
        kyc.verified_by = request.user
        kyc.verified_at = timezone.now()
        kyc.save()

        # Auto-activate user
        if kyc.status == 'APPROVED':
            kyc.user.status = 'ACTIVE'
            kyc.user.save()

        return Response(KYCSerializer(kyc).data)