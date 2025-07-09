from rest_framework import serializers
from apps.clients.models import Client
from apps.schedules.models import Booking

class EmployeeDashboardOverviewSerializer(serializers.Serializer):
    total_clients = serializers.IntegerField()
    appointments_today = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_ticket = serializers.DecimalField(max_digits=10, decimal_places=2)
    clients_growth = serializers.FloatField()
    revenue_growth = serializers.FloatField()
    appointments_growth = serializers.FloatField()
    avg_ticket_change = serializers.FloatField()
    user_name = serializers.CharField()

class EmployeeRevenueChartSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    revenue = serializers.ListField(child=serializers.DecimalField(max_digits=10, decimal_places=2))
    bookings = serializers.ListField(child=serializers.IntegerField())
    clients = serializers.ListField(child=serializers.IntegerField())

class EmployeeAIInsightSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    priority = serializers.IntegerField()

class EmployeeTopClientSerializer(serializers.ModelSerializer):
    booking_count = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2, source='top_total_spent')
    class Meta:
        model = Client
        fields = ['id', 'name', 'phone', 'booking_count', 'total_spent', 'status'] 