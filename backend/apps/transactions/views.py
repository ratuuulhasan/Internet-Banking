from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
import requests
from django.conf import settings

from .models import Transaction
from .serializers import TransactionSerializer, TransferSerializer
from apps.accounts.models import Account
from apps.audit.utils import log_action


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        account_ids = user.accounts.values_list('account_id', flat=True)
        return Transaction.objects.filter(
            from_account_id__in=account_ids
        ) | Transaction.objects.filter(to_account_id__in=account_ids)


class TransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Verify OTP (placeholder — real OTP app er sathe integrate korte hobe)
        from apps.otp_service.utils import verify_otp
        if not verify_otp(request.user, data['otp_code'], 'TRANSFER'):
            return Response({'error': 'Invalid or expired OTP'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            with db_transaction.atomic():
                # Lock source account
                src = Account.objects.select_for_update().get(
                    account_id=data['from_account_id'],
                    user=request.user,
                    status='ACTIVE'
                )

                # Find destination
                try:
                    dst = Account.objects.select_for_update().get(
                        account_number=data['to_account_number'],
                        status='ACTIVE'
                    )
                except Account.DoesNotExist:
                    return Response({'error': 'Destination account not found'},
                                    status=status.HTTP_404_NOT_FOUND)

                if src.account_id == dst.account_id:
                    return Response({'error': 'Cannot transfer to same account'},
                                    status=status.HTTP_400_BAD_REQUEST)

                amount = data['amount']

                # Business rules
                if src.balance < amount:
                    return Response({'error': 'Insufficient balance'},
                                    status=status.HTTP_400_BAD_REQUEST)

                if amount > Decimal('200000'):
                    return Response({'error': 'Per transaction limit exceeded (৳2,00,000)'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Create transaction record first
                txn = Transaction.objects.create(
                    from_account=src,
                    to_account=dst,
                    transaction_type='TRANSFER',
                    amount=amount,
                    status='PENDING',
                    description=data.get('description', ''),
                    otp_verified=True,
                    ip_address=self.get_client_ip(request),
                )

                # AI fraud check
                fraud_score = self._check_fraud(txn, src)
                txn.fraud_score = fraud_score

                if fraud_score and fraud_score > 0.8:
                    txn.status = 'HELD'
                    txn.save()
                    log_action(request.user, 'TRANSFER_HELD', 'Transaction', txn.transaction_id,
                               {'fraud_score': fraud_score})
                    return Response({
                        'message': 'Transaction held for manual review due to security check.',
                        'reference_no': txn.reference_no,
                        'status': 'HELD',
                    }, status=status.HTTP_202_ACCEPTED)

                # Perform transfer
                src.balance -= amount
                dst.balance += amount
                src.save()
                dst.save()

                txn.status = 'SUCCESS'
                txn.completed_at = timezone.now()
                txn.save()

                log_action(request.user, 'TRANSFER_SUCCESS', 'Transaction', txn.transaction_id,
                           {'amount': str(amount), 'to': dst.account_number})

                return Response({
                    'message': 'Transfer successful',
                    'reference_no': txn.reference_no,
                    'status': 'SUCCESS',
                    'amount': str(amount),
                    'new_balance': str(src.balance),
                }, status=status.HTTP_201_CREATED)

        except Account.DoesNotExist:
            return Response({'error': 'Account not found'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def get_client_ip(request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def _check_fraud(txn, account):
        """Call AI microservice"""
        try:
            response = requests.post(
                f"{settings.AI_SERVICE_URL}/fraud/predict",
                json={
                    'amount': float(txn.amount),
                    'hour': txn.created_at.hour,
                    'txn_type': 1,
                    'device_change': 0,
                    'location_change': 0,
                    'account_age_days': (timezone.now() - account.opened_at).days,
                },
                timeout=3
            )
            if response.status_code == 200:
                return response.json().get('fraud_score', 0)
        except Exception:
            pass
        return 0.0