from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.settings_auto_view, name='settings_page'),
    path('api/profile/', views.SettingsProfileAPIView.as_view(), name='settings_profile_api'),
    path('api/business/', views.SettingsBusinessAPIView.as_view(), name='settings_business_api'),
    path('api/change-password/', views.ChangePasswordAPIView.as_view(), name='settings_change_password_api'),
    
    # Новые API endpoints для настроек
    path('api/notifications/user/', views.UserNotificationSettingsAPIView.as_view(), name='user_notifications_api'),
    path('api/notifications/business/', views.BusinessNotificationSettingsAPIView.as_view(), name='business_notifications_api'),
    path('api/booking-settings/', views.BookingSettingsAPIView.as_view(), name='booking_settings_api'),
    path('api/preferences/', views.UserPreferencesAPIView.as_view(), name='user_preferences_api'),
    
    # WhatsApp верификация телефона
    path('api/send-phone-verification/', views.SendPhoneVerificationCodeAPIView.as_view(), name='send_phone_verification'),
    path('api/verify-phone-code/', views.VerifyPhoneCodeAPIView.as_view(), name='verify_phone_code'),
] 