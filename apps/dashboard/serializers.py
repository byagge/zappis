from rest_framework import serializers
from .models import BusinessStats, FinanceRecord, ActivityLog
from apps.businesses.models import Business
from apps.accounts.models import User

class BusinessStatsSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta:
        model = BusinessStats
        fields = ['business_name', 'total_clients', 'total_appointments', 'total_revenue', 'avg_ticket', 'updated_at']

class FinanceRecordSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = FinanceRecord
        fields = ['id', 'business_name', 'amount', 'date', 'description', 'is_income', 'type_display']
    
    def get_type_display(self, obj):
        return 'Доход' if obj.is_income else 'Расход'

class ActivityLogSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityLog
        fields = ['id', 'business_name', 'user_name', 'action', 'timestamp', 'time_ago', 'extra']
    
    def get_time_ago(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.timestamp
        
        if diff.days > 0:
            return f"{diff.days} дней назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} часов назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} минут назад"
        else:
            return "Только что"

class DashboardOverviewSerializer(serializers.Serializer):
    """Сериализатор для общей статистики dashboard"""
    total_clients = serializers.IntegerField()
    appointments_today = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_ticket = serializers.DecimalField(max_digits=10, decimal_places=2)
    clients_growth = serializers.FloatField()
    revenue_growth = serializers.FloatField()
    appointments_growth = serializers.FloatField()
    avg_ticket_change = serializers.FloatField()
    total_employees = serializers.IntegerField()
    total_services = serializers.IntegerField()
    active_businesses = serializers.IntegerField()
    user_name = serializers.CharField()

class RevenueChartSerializer(serializers.Serializer):
    """Сериализатор для графика доходов, записей и клиентов"""
    labels = serializers.ListField(child=serializers.CharField())
    revenue = serializers.ListField(child=serializers.DecimalField(max_digits=10, decimal_places=2))
    bookings = serializers.ListField(child=serializers.IntegerField())
    clients = serializers.ListField(child=serializers.IntegerField())

class RecentActivitySerializer(serializers.Serializer):
    """Сериализатор для последних действий"""
    activities = ActivityLogSerializer(many=True)

class AIInsightSerializer(serializers.Serializer):
    """Сериализатор для ИИ-советов"""
    title = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    priority = serializers.IntegerField() 