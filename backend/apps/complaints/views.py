from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Complaint
from .serializers import ComplaintSerializer, ComplaintUpdateSerializer
from apps.users.permissions import IsEmployee
from apps.notifications.utils import send_notification


class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['ADMIN', 'EMPLOYEE']:
            return Complaint.objects.all()
        return Complaint.objects.filter(user=user)

    def perform_create(self, serializer):
        complaint = serializer.save(user=self.request.user)
        send_notification(
            complaint.user,
            "Complaint Registered",
            f"Your ticket #{complaint.ticket_id} has been created.",
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsEmployee])
    def update_status(self, request, pk=None):
        complaint = self.get_object()
        serializer = ComplaintUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        complaint.status = data['status']
        if 'priority' in data:
            complaint.priority = data['priority']
        if 'assigned_to' in data:
            complaint.assigned_to_id = data['assigned_to']
        if 'resolution_note' in data:
            complaint.resolution_note = data['resolution_note']
        complaint.save()

        send_notification(
            complaint.user,
            f"Ticket #{complaint.ticket_id} Updated",
            f"Status: {complaint.status}. {complaint.resolution_note}",
        )
        return Response(ComplaintSerializer(complaint).data)