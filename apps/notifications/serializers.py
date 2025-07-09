from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'type', 'title', 'message', 'date', 'is_read', 'is_important', 'reminder_time', 'event_date', 'created_at']
        read_only_fields = ['id', 'user', 'created_at'] 