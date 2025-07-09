from rest_framework import serializers
from .models import Service, ServiceCategory
from apps.businesses.models import Business
# from apps.businesses.serializers import BusinessShortSerializer

class ServiceCategorySerializer(serializers.ModelSerializer):
    services_count = serializers.SerializerMethodField()
    business_id = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(),
        source='business',
        write_only=True
    )
    
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'services_count', 'business_id', 'created_at', 'updated_at']
    
    def get_services_count(self, obj):
        return obj.services.count()

class ServiceCategoryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name']

class ServiceSerializer(serializers.ModelSerializer):
    category = ServiceCategoryShortSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(),
        source='category',
        write_only=True,
        allow_null=True,
        required=False
    )
    business_id = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(),
        source='business',
        write_only=True
    )
    formatted_price = serializers.ReadOnlyField()
    formatted_duration = serializers.ReadOnlyField()
    is_active = serializers.BooleanField(default=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'category', 'category_id',
            'business_id',
            'price', 'duration', 'is_active', 'formatted_price',
            'formatted_duration', 'created_at', 'updated_at'
        ]

class ServiceShortSerializer(serializers.ModelSerializer):
    category = ServiceCategoryShortSerializer(read_only=True)
    formatted_price = serializers.ReadOnlyField()
    formatted_duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Service
        fields = ['id', 'name', 'category', 'price', 'duration', 'formatted_price', 'formatted_duration'] 