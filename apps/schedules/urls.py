from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, booking_page, SendWhatsAppMessageAPIView, SendReminderAPIView
from django.urls import path, include

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', booking_page, name='booking_page'),
    path('api/', include(router.urls)),
    path('api/send-whatsapp/', SendWhatsAppMessageAPIView.as_view(), name='send_whatsapp'),
    path('api/send-reminder/', SendReminderAPIView.as_view(), name='send_reminder'),
] 