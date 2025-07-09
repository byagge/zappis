from django.contrib import admin
from .models import UserNotificationSettings, BusinessNotificationSettings, BookingSettings, UserPreferences
 
# Register your models here. 

@admin.register(UserNotificationSettings)
class UserNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_notifications', 'sms_notifications', 'whatsapp_notifications', 'telegram_notifications', 'updated_at']
    list_filter = ['email_notifications', 'sms_notifications', 'whatsapp_notifications', 'telegram_notifications']
    search_fields = ['user__full_name', 'user__email', 'user__phone_number']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(BusinessNotificationSettings)
class BusinessNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['business', 'email_notifications', 'sms_notifications', 'whatsapp_notifications', 'telegram_notifications', 'updated_at']
    list_filter = ['email_notifications', 'sms_notifications', 'whatsapp_notifications', 'telegram_notifications']
    search_fields = ['business__name', 'business__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    list_display = ['business', 'default_slot_duration', 'buffer_time', 'auto_confirm_bookings', 'updated_at']
    list_filter = ['default_slot_duration', 'buffer_time', 'auto_confirm_bookings']
    search_fields = ['business__name', 'business__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'language', 'timezone', 'updated_at']
    list_filter = ['theme', 'language', 'timezone']
    search_fields = ['user__full_name', 'user__email', 'user__phone_number']
    readonly_fields = ['created_at', 'updated_at'] 