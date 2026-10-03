from django.db import transaction as db_txn
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Bill
from .serializers import BillSerializer, BillPaymentSerializer
from apps.accounts.models import Account
from apps.transactions.models import Transaction
from apps.otp_service.utils import verify_otp
from apps.audit.utils import log_action


class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bill.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def pay(self, request):
        serializer = BillPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not verify_otp(request.user, data['otp_code'], 'BILL_PAYMENT'):
            return Response({'error': 'Invalid or expired OTP'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            with db_txn.atomic():
                bill = Bill.objects.select_for_update().get(
                    bill_id=data['bill_id'], user=request.user, status='UNPAID'
                )
                src = Account.objects.select_for_update().get(
                    account_id=data['from_account_id'], user=request.user, status='ACTIVE'
                )

                if src.balance < bill.amount:
                    return Response({'error': 'Insufficient balance'},
                                    status=status.HTTP_400_BAD_REQUEST)

                txn = Transaction.objects.create(
                    from_account=src,
                    transaction_type='BILL_PAYMENT',
                    amount=bill.amount,
                    status='SUCCESS',
                    description=f'Bill payment: {bill.biller_name}',
                    otp_verified=True,
                    completed_at=timezone.now(),
                )

                src.balance -= bill.amount
                src.save()

                bill.status = 'PAID'
                bill.paid_transaction = txn
                bill.save()

                log_action(request.user, 'BILL_PAID', 'Bill', bill.bill_id,
                           {'amount': str(bill.amount), 'txn': txn.reference_no})

                return Response({
                    'message': 'Bill paid successfully',
                    'reference_no': txn.reference_no,
                    'new_balance': str(src.balance),
                })
        except Bill.DoesNotExist:
            return Response({'error': 'Bill not found or already paid'},
                            status=status.HTTP_404_NOT_FOUND)
        except Account.DoesNotExist:
            return Response({'error': 'Account not found'},
                            status=status.HTTP_404_NOT_FOUND)