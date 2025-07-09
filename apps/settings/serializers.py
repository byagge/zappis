from rest_framework import serializers
from apps.accounts.models import User
from apps.businesses.models import Business, BusinessType, BusinessSubtype
from .models import UserNotificationSettings, BusinessNotificationSettings, BookingSettings, UserPreferences

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'avatar', 'preferred_language', 'user_timezone', 'city', 'country'
        ]

class BusinessTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessType
        fields = ['id', 'name']

class BusinessSubtypeSerializer(serializers.ModelSerializer):
    business_type = BusinessTypeSerializer(read_only=True)
    class Meta:
        model = BusinessSubtype
        fields = ['id', 'name', 'icon', 'business_type']

class BusinessSettingsSerializer(serializers.ModelSerializer):
    type = serializers.PrimaryKeyRelatedField(queryset=BusinessType.objects.all(), required=False, allow_null=True)
    subtype = serializers.PrimaryKeyRelatedField(queryset=BusinessSubtype.objects.all(), required=False, allow_null=True)
    type_detail = BusinessTypeSerializer(source='type', read_only=True)
    subtype_detail = BusinessSubtypeSerializer(source='subtype', read_only=True)

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'description', 'type', 'type_detail', 'subtype', 'subtype_detail', 'employees_count', 'address', 'city', 'country',
            'phone', 'phone_contact', 'email', 'website_url', 'instagram', 'timezone', 'language', 'is_active', 'username', 'referral_code'
        ]

class UserNotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationSettings
        fields = [
            'email_notifications', 'sms_notifications', 'whatsapp_notifications', 'telegram_notifications'
        ]

class BusinessNotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessNotificationSettings
        fields = [
            'email_notifications', 'sms_notifications', 'whatsapp_notifications', 'telegram_notifications'
        ]

class BookingSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingSettings
        fields = [
            'default_slot_duration', 'buffer_time', 'auto_confirm_bookings'
        ]

class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = [
            'theme', 'language', 'timezone'
        ]

# from rest_framework import serializers
# from .models import ...

# class ...Serializer(serializers.ModelSerializer):
#     class Meta:
#         model = ...
#         fields = '__all__' 