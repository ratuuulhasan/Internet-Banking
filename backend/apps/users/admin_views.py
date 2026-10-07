from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .serializers import UserSerializer
from .permissions import IsAdmin
from apps.audit.utils import log_action

User = get_user_model()


class AdminUserViewSet(viewsets.ModelViewSet):
    """Admin-only user management"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.all().order_by('-created_at')

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get('search')
        role = self.request.query_params.get('role')
        status_filter = self.request.query_params.get('status')
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(full_name__icontains=search) |
                Q(phone__icontains=search)
            )
        if role:
            qs = qs.filter(role=role)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        user = self.get_object()
        if user.role in ['ADMIN', 'SYS_ADMIN']:
            return Response({'error': 'Cannot block admin'},
                            status=status.HTTP_400_BAD_REQUEST)
        user.status = 'BLOCKED'
        user.is_active = False
        user.save()
        log_action(request.user, 'USER_BLOCKED', 'User', user.user_id)
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        user = self.get_object()
        user.status = 'ACTIVE'
        user.is_active = True
        user.save()
        log_action(request.user, 'USER_UNBLOCKED', 'User', user.user_id)
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get('role')
        if new_role not in ['CUSTOMER', 'ADMIN', 'EMPLOYEE', 'AUDITOR', 'SYS_ADMIN']:
            return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
        user.role = new_role
        user.save()
        log_action(request.user, 'ROLE_CHANGED', 'User', user.user_id, {'new_role': new_role})
        return Response(UserSerializer(user).data)


class AdminDashboardStatsView(APIView):
    """Returns summary numbers for admin dashboard"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from apps.accounts.models import Account
        from apps.transactions.models import Transaction
        from apps.kyc.models import KYC
        from apps.loans.models import Loan
        from apps.complaints.models import Complaint

        today = timezone.now().date()
        last_30_days = timezone.now() - timedelta(days=30)

        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(status='ACTIVE').count(),
            'pending_kyc': KYC.objects.filter(status='PENDING').count(),
            'total_accounts': Account.objects.count(),
            'total_balance': float(Account.objects.aggregate(s=Sum('balance'))['s'] or 0),
            'txns_today': Transaction.objects.filter(created_at__date=today).count(),
            'txns_30d': Transaction.objects.filter(created_at__gte=last_30_days).count(),
            'held_txns': Transaction.objects.filter(status='HELD').count(),
            'pending_loans': Loan.objects.filter(status='PENDING').count(),
            'open_complaints': Complaint.objects.filter(
                status__in=['OPEN', 'IN_PROGRESS']
            ).count(),
        }
        return Response(stats)


class AdminRecentActivityView(APIView):
    """Recent 20 activities across the platform"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from apps.transactions.models import Transaction
        from apps.audit.models import AuditLog

        recent_txns = Transaction.objects.select_related(
            'from_account__user'
        ).order_by('-created_at')[:10]

        txn_data = [{
            'type': 'transaction',
            'reference': t.reference_no,
            'amount': float(t.amount),
            'status': t.status,
            'user': t.from_account.user.email,
            'time': t.created_at,
        } for t in recent_txns]

        return Response({'recent_transactions': txn_data})


class AdminFraudAlertsView(APIView):
    """List all held/fraud-suspect transactions"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from apps.transactions.models import Transaction
        from apps.transactions.serializers import TransactionSerializer

        held = Transaction.objects.filter(
            status='HELD'
        ).select_related('from_account__user', 'to_account__user').order_by('-created_at')

        return Response(TransactionSerializer(held, many=True).data)

    def post(self, request):
        """Approve or reject a held transaction"""
        from apps.transactions.models import Transaction
        from decimal import Decimal

        txn_id = request.data.get('transaction_id')
        decision = request.data.get('decision')  # 'APPROVE' or 'REJECT'

        if decision not in ['APPROVE', 'REJECT']:
            return Response({'error': 'Invalid decision'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from django.db import transaction as db_txn
            with db_txn.atomic():
                txn = Transaction.objects.select_for_update().get(
                    transaction_id=txn_id, status='HELD'
                )

                if decision == 'APPROVE':
                    from apps.accounts.models import Account
                    src = Account.objects.select_for_update().get(
                        account_id=txn.from_account_id
                    )
                    dst = Account.objects.select_for_update().get(
                        account_id=txn.to_account_id
                    )

                    if src.balance < txn.amount:
                        return Response({'error': 'Insufficient balance now'},
                                        status=status.HTTP_400_BAD_REQUEST)

                    src.balance -= txn.amount
                    dst.balance += txn.amount
                    src.save()
                    dst.save()

                    txn.status = 'SUCCESS'
                    txn.completed_at = timezone.now()
                    txn.save()

                    log_action(request.user, 'FRAUD_APPROVED', 'Transaction', txn.transaction_id)
                else:
                    txn.status = 'REVERSED'
                    txn.save()
                    log_action(request.user, 'FRAUD_REJECTED', 'Transaction', txn.transaction_id)

            return Response({'message': f'Transaction {decision}D successfully'})

        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'},
                            status=status.HTTP_404_NOT_FOUND)