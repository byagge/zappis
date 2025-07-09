from rest_framework import serializers
from .models import Website
from apps.schedules.models import Booking

class WebsiteSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_id = serializers.IntegerField(source='business.id', read_only=True)
    class Meta:
        model = Website
        fields = ['id', 'url', 'business', 'business_id', 'business_name', 'bookings_count', 'website_bookings_count', 'views_count']

class WebsiteBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'customer_name', 'customer_phone', 'customer_email', 'service', 'specialist', 'date', 'time', 'comment'] 