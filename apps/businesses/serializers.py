from rest_framework import serializers
from .models import Business, BusinessWorkingHour
from django.contrib.auth import get_user_model

User = get_user_model()

class BusinessRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Business
        fields = [
            'username', 'name', 'password', 'email', 'phone', 'type', 'city', 'country',
            'address', 'description', 'logo', 'timezone', 'language', 'referral_code', 'owner'
        ]
        extra_kwargs = {
            'referral_code': {'read_only': True},
            'logo': {'required': False, 'allow_null': True},
            'owner': {'required': False},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        owner = validated_data.get('owner', None)
        business = Business(**validated_data)
        if owner:
            business.owner = owner
        business.save()
        # Можно добавить логику для создания пользователя, если нужно
        return business 

class BusinessWorkingHourSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)
    class Meta:
        model = BusinessWorkingHour
        fields = ['id', 'day', 'day_display', 'start', 'end', 'enabled'] 