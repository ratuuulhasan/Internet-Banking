import requests
from django.conf import settings as django_settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Loan
from .serializers import LoanSerializer, LoanDecisionSerializer
from apps.users.permissions import IsAdmin
from apps.audit.utils import log_action


class LoanViewSet(viewsets.ModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'EMPLOYEE']:
            return Loan.objects.all()
        return Loan.objects.filter(user=user)

    def perform_create(self, serializer):
        loan = serializer.save(user=self.request.user)
        # Calculate EMI
        P = float(loan.principal_amount)
        r = float(loan.interest_rate) / 100 / 12
        n = loan.tenure_months
        if r > 0:
            emi = P * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
        else:
            emi = P / n
        loan.monthly_emi = round(emi, 2)
        # AI credit score
        loan.ai_credit_score = self._get_credit_score(loan)
        loan.save()

    @staticmethod
    def _get_credit_score(loan):
        try:
            r = requests.post(
                f"{django_settings.AI_SERVICE_URL}/credit/score",
                json={
                    'income': float(loan.principal_amount) / loan.tenure_months,
                    'existing_loans': Loan.objects.filter(user=loan.user, status='ACTIVE').count(),
                    'tenure_months': loan.tenure_months,
                    'interest_rate': float(loan.interest_rate),
                },
                timeout=3
            )
            if r.status_code == 200:
                return r.json().get('score')
        except Exception:
            pass
        return None

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def decide(self, request, pk=None):
        loan = self.get_object()
        serializer = LoanDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan.status = serializer.validated_data['status']
        loan.approved_by = request.user
        loan.approved_at = timezone.now()
        if loan.status == 'APPROVED':
            loan.status = 'ACTIVE'
        loan.save()
        log_action(request.user, f'LOAN_{loan.status}', 'Loan', loan.loan_id)
        return Response(LoanSerializer(loan).data)