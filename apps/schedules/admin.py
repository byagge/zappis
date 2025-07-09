from django.contrib import admin
from .models import Booking
from apps.clients.models import Client

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('client', 'service', 'master', 'date', 'start_time', 'end_time', 'price')
    list_filter = ('master', 'date')
    search_fields = ('client__name', 'client__phone')
    fields = ('client', 'service', 'master', 'date', 'start_time', 'end_time', 'price', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
