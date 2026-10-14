"""
User views — Authentication, registration, profile.
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ============================================================
# REGISTRATION
# ============================================================
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # ---- Send welcome email (async) ----
        try:
            from apps.notifications.tasks import send_welcome_email_task
            send_welcome_email_task.delay(user.user_id)
        except Exception as e:
            logger.warning(f"Welcome email failed for {user.email}: {e}")

        # ---- Audit log ----
        try:
            from apps.audit.utils import log_action
            log_action(
                user,
                'USER_REGISTERED',
                'User',
                user.user_id,
                {'email': user.email, 'phone': user.phone},
                request=request,
            )
        except Exception:
            pass

        return Response({
            'message': 'Registration successful. Await KYC verification.',
            'user_id': user.user_id,
            'email': user.email,
        }, status=status.HTTP_201_CREATED)


# ============================================================
# PROFILE
# ============================================================
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# ============================================================
# CHANGE PASSWORD
# ============================================================
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        # ---- Audit log ----
        try:
            from apps.audit.utils import log_action
            log_action(
                request.user,
                'PASSWORD_CHANGED',
                'User',
                request.user.user_id,
                request=request,
            )
        except Exception:
            pass

        # ---- Notify user (async) ----
        try:
            from apps.notifications.tasks import send_transaction_notification_task
            send_transaction_notification_task.delay(
                request.user.user_id,
                {
                    'reference_no': 'PWD-CHANGE',
                    'amount': '0',
                    'transaction_type': 'SECURITY',
                    'status': 'SUCCESS',
                    'created_at': timezone.now().strftime('%Y-%m-%d %H:%M'),
                    'new_balance': 'N/A',
                }
            )
        except Exception:
            pass

        return Response({'message': 'Password changed successfully.'})


# ============================================================
# LOGOUT
# ============================================================
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh = request.data.get('refresh')
            if refresh:
                RefreshToken(refresh).blacklist()
        except Exception:
            pass
        return Response({'message': 'Logged out.'})