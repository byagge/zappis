from rest_framework import serializers
from .models import Client
from apps.schedules.models import Booking
from django.db.models import Sum, Avg
from django.utils import timezone

class ClientSerializer(serializers.ModelSerializer):
    total_visits = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    activity_status = serializers.SerializerMethodField()
    average_check = serializers.SerializerMethodField()
    next_visit = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'phone', 'email', 'status', 'business', 'notes', 'city', 
            'total_visits', 'total_spent', 'activity_status', 'average_check', 
            'next_visit', 'created_at', 'updated_at'
        ]
    
    def get_total_visits(self, obj):
        """Подсчитываем общее количество записей клиента"""
        return Booking.objects.filter(client=obj).count()
    
    def get_total_spent(self, obj):
        """Подсчитываем общую сумму потраченную клиентом"""
        total = Booking.objects.filter(client=obj).aggregate(total=Sum('price'))['total']
        return float(total) if total else 0.0
    
    def get_activity_status(self, obj):
        """Возвращает статус активности клиента"""
        return obj.get_activity_status()
    
    def get_average_check(self, obj):
        """Возвращает средний чек клиента"""
        avg = Booking.objects.filter(client=obj).aggregate(avg=Avg('price'))['avg']
        return float(avg) if avg else 0.0
    
    def get_next_visit(self, obj):
        """Получаем дату следующего визита клиента"""
        today = timezone.now().date()
        next_booking = Booking.objects.filter(
            client=obj, date__gte=today
        ).order_by('date', 'start_time').first()
        return next_booking.date if next_booking else None 