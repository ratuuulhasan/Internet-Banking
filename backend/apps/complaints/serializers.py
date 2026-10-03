from rest_framework import serializers
from .models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Complaint
        fields = ['ticket_id', 'user', 'user_email', 'subject', 'description',
                  'status', 'priority', 'assigned_to', 'resolution_note',
                  'created_at', 'updated_at']
        read_only_fields = ['ticket_id', 'user', 'status', 'assigned_to',
                            'resolution_note', 'created_at', 'updated_at']


class ComplaintUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'])
    priority = serializers.ChoiceField(choices=['LOW', 'MEDIUM', 'HIGH'], required=False)
    assigned_to = serializers.IntegerField(required=False, allow_null=True)
    resolution_note = serializers.CharField(required=False, allow_blank=True)