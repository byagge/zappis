from django.db import models
from apps.businesses.models import Business
from apps.clients.models import Client
from apps.schedules.models import Booking
from apps.services.models import Service
from apps.employees.models import Employee
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, date
import json

class AnalyticsReport(models.Model):
    """Модель для хранения отчетов аналитики"""
    REPORT_TYPES = [
        ('revenue', 'Выручка'),
        ('clients', 'Клиенты'),
        ('services', 'Услуги'),
        ('employees', 'Сотрудники'),
        ('bookings', 'Записи'),
        ('custom', 'Пользовательский'),
    ]
    
    PERIOD_TYPES = [
        ('daily', 'День'),
        ('weekly', 'Неделя'),
        ('monthly', 'Месяц'),
        ('quarterly', 'Квартал'),
        ('yearly', 'Год'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name="Бизнес")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name="Тип отчета")
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, verbose_name="Период")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    data = models.JSONField(default=dict, verbose_name="Данные отчета")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Отчет аналитики"
        verbose_name_plural = "Отчеты аналитики"
        unique_together = ['business', 'report_type', 'period_type', 'start_date', 'end_date']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.start_date} - {self.end_date}"

class AnalyticsDashboard(models.Model):
    """Модель для настройки дашборда аналитики"""
    business = models.OneToOneField(Business, on_delete=models.CASCADE, verbose_name="Бизнес")
    widgets = models.JSONField(default=list, verbose_name="Виджеты")
    layout = models.JSONField(default=dict, verbose_name="Макет")
    settings = models.JSONField(default=dict, verbose_name="Настройки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Дашборд аналитики"
        verbose_name_plural = "Дашборды аналитики"
    
    def __str__(self):
        return f"Дашборд {self.business.name}"

class AnalyticsMetric(models.Model):
    """Модель для хранения метрик аналитики"""
    METRIC_TYPES = [
        ('revenue', 'Выручка'),
        ('bookings', 'Количество записей'),
        ('clients', 'Количество клиентов'),
        ('services', 'Количество услуг'),
        ('avg_check', 'Средний чек'),
        ('conversion', 'Конверсия'),
        ('retention', 'Удержание'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, verbose_name="Бизнес")
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES, verbose_name="Тип метрики")
    value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Значение")
    date = models.DateField(verbose_name="Дата")
    period = models.CharField(max_length=20, verbose_name="Период")
    metadata = models.JSONField(default=dict, verbose_name="Метаданные")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Метрика аналитики"
        verbose_name_plural = "Метрики аналитики"
        unique_together = ['business', 'metric_type', 'date', 'period']
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.date}"

class AnalyticsService:
    """Сервисный класс для работы с аналитикой"""
    
    def __init__(self, business):
        self.business = business
    
    def get_revenue_data(self, start_date, end_date, period='daily'):
        """Получение данных о выручке"""
        bookings = Booking.objects.filter(
            business=self.business,
            date__range=[start_date, end_date],
            status='completed'
        )
        
        if period == 'daily':
            return bookings.values('date').annotate(
                revenue=Sum('price'),
                bookings_count=Count('id')
            ).order_by('date')
        elif period == 'weekly':
            return bookings.extra(
                select={'week': "EXTRACT(week FROM date)"}
            ).values('week').annotate(
                revenue=Sum('price'),
                bookings_count=Count('id')
            ).order_by('week')
        elif period == 'monthly':
            return bookings.extra(
                select={'month': "EXTRACT(month FROM date)", 'year': "EXTRACT(year FROM date)"}
            ).values('month', 'year').annotate(
                revenue=Sum('price'),
                bookings_count=Count('id')
            ).order_by('year', 'month')
        
        return []
    
    def get_clients_data(self, start_date, end_date):
        """Получение данных о клиентах"""
        clients = Client.objects.filter(business=self.business)
        
        # Новые клиенты
        new_clients = clients.filter(created_at__date__range=[start_date, end_date])
        
        # Активные клиенты (с записями в период)
        active_clients = clients.filter(
            bookings__date__range=[start_date, end_date]
        ).distinct()
        
        # VIP клиенты
        vip_clients = clients.filter(status='vip')
        
        return {
            'total': clients.count(),
            'new': new_clients.count(),
            'active': active_clients.count(),
            'vip': vip_clients.count(),
            'growth_rate': self._calculate_growth_rate(new_clients, start_date, end_date)
        }
    
    def get_services_data(self, start_date, end_date):
        """Получение данных об услугах"""
        bookings = Booking.objects.filter(
            business=self.business,
            date__range=[start_date, end_date],
            status='completed'
        )
        
        services_data = bookings.values('service__name').annotate(
            bookings_count=Count('id'),
            total_revenue=Sum('price'),
            avg_price=Avg('price')
        ).order_by('-total_revenue')
        
        return services_data
    
    def get_employees_data(self, start_date, end_date):
        """Получение данных о сотрудниках"""
        bookings = Booking.objects.filter(
            business=self.business,
            date__range=[start_date, end_date],
            status='completed'
        )
        
        employees_data = bookings.values('employee__name').annotate(
            bookings_count=Count('id'),
            total_revenue=Sum('price'),
            avg_price=Avg('price')
        ).order_by('-total_revenue')
        
        return employees_data
    
    def get_bookings_data(self, start_date, end_date):
        """Получение данных о записях"""
        bookings = Booking.objects.filter(
            business=self.business,
            date__range=[start_date, end_date]
        )
        
        total_bookings = bookings.count()
        completed_bookings = bookings.filter(status='completed').count()
        cancelled_bookings = bookings.filter(status='cancelled').count()
        
        return {
            'total': total_bookings,
            'completed': completed_bookings,
            'cancelled': cancelled_bookings,
            'completion_rate': (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0,
            'daily_average': total_bookings / max((end_date - start_date).days, 1)
        }
    
    def get_dashboard_summary(self):
        """Получение сводки для дашборда"""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)
        
        # Текущий месяц
        current_month_revenue = self.get_revenue_data(month_start, today)
        current_month_clients = self.get_clients_data(month_start, today)
        
        # Прошлый месяц
        last_month_revenue = self.get_revenue_data(last_month_start, last_month_end)
        last_month_clients = self.get_clients_data(last_month_start, last_month_end)
        
        return {
            'current_month': {
                'revenue': sum(item['revenue'] for item in current_month_revenue),
                'new_clients': current_month_clients['new'],
                'bookings': sum(item['bookings_count'] for item in current_month_revenue)
            },
            'last_month': {
                'revenue': sum(item['revenue'] for item in last_month_revenue),
                'new_clients': last_month_clients['new'],
                'bookings': sum(item['bookings_count'] for item in last_month_revenue)
            },
            'growth': {
                'revenue': self._calculate_percentage_change(
                    sum(item['revenue'] for item in last_month_revenue),
                    sum(item['revenue'] for item in current_month_revenue)
                ),
                'clients': self._calculate_percentage_change(
                    last_month_clients['new'],
                    current_month_clients['new']
                )
            }
        }
    
    def _calculate_growth_rate(self, queryset, start_date, end_date):
        """Расчет темпа роста"""
        period_days = (end_date - start_date).days
        if period_days == 0:
            return 0
        
        count = queryset.count()
        return count / period_days
    
    def _calculate_percentage_change(self, old_value, new_value):
        """Расчет процентного изменения"""
        if old_value == 0:
            return 100 if new_value > 0 else 0
        return ((new_value - old_value) / old_value) * 100 