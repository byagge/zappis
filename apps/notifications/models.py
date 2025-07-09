from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("reminder", "Напоминание"),
        ("event", "Событие"),
        ("alert", "Оповещение"),
        ("system", "Системное"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default="reminder")
    title = models.CharField(max_length=255)
    message = models.TextField()
    date = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    reminder_time = models.CharField(max_length=100, blank=True, null=True)
    event_date = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user}: {self.title}"
