from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['notification_id', 'title', 'message', 'channel',
                  'status', 'is_read', 'sent_at', 'created_at']
        read_only_fields = ['notification_id', 'status', 'sent_at', 'created_at']