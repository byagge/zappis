from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'is_important', 'is_read', 'date', 'created_at')
    list_filter = ('type', 'is_important', 'is_read', 'date', 'created_at')
    search_fields = ('user__username', 'title', 'message')
