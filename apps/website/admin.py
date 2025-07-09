from django.contrib import admin
from .models import Website, WebsiteBooking

@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ("id", "business", "url", "views_count", "bookings_count", "website_bookings_count")
    search_fields = ("url", "business__name")
    list_filter = ("business",)

@admin.register(WebsiteBooking)
class WebsiteBookingAdmin(admin.ModelAdmin):
    list_display = ("id", "website", "customer_name", "customer_phone", "service", "date", "time", "created_at")
    search_fields = ("customer_name", "customer_phone", "service", "website__url")
    list_filter = ("website", "date")
