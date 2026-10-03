from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .utils import generate_otp


class RequestOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        purpose = request.data.get('purpose', 'TRANSFER')
        generate_otp(request.user, purpose)
        return Response({'message': 'OTP sent to your registered phone/email.'})