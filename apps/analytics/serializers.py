from rest_framework import serializers
from .models import AnalyticsReport, AnalyticsDashboard, AnalyticsMetric
from apps.clients.models import Client
from apps.schedules.models import Booking
from apps.services.models import Service
from apps.employees.models import Employee
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from django.utils import timezone

class AnalyticsReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsReport
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class AnalyticsDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsDashboard
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class AnalyticsMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsMetric
        fields = '__all__'
        read_only_fields = ['created_at']

class RevenueDataSerializer(serializers.Serializer):
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    bookings_count = serializers.IntegerField()

class ClientsDataSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    new = serializers.IntegerField()
    active = serializers.IntegerField()
    vip = serializers.IntegerField()
    growth_rate = serializers.FloatField()

class ServicesDataSerializer(serializers.Serializer):
    service_name = serializers.CharField()
    bookings_count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class EmployeesDataSerializer(serializers.Serializer):
    employee_name = serializers.CharField()
    bookings_count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class BookingsDataSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    daily_average = serializers.FloatField()

class DashboardSummarySerializer(serializers.Serializer):
    current_month = serializers.DictField()
    last_month = serializers.DictField()
    growth = serializers.DictField()

class ChartDataSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())

class AnalyticsFilterSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    period = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly', 'quarterly', 'yearly'],
        default='daily'
    )
    report_type = serializers.ChoiceField(
        choices=['revenue', 'clients', 'services', 'employees', 'bookings'],
        required=False
    ) 