from django.db import models
from apps.main.models import City
from apps.businesses.models import Business
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class Client(models.Model):
    STATUS_CHOICES = [
        ("new", "Новый"),
        ("vip", "VIP"),
        ("regular", "Постоянный"),
        ("inactive", "Неактивный"),
    ]

    name = models.CharField(max_length=255, verbose_name="Имя")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус")
    notes = models.TextField(blank=True, null=True, verbose_name="Примечания")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Город")
    business = models.ForeignKey(Business, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Бизнес")
    total_visits = models.PositiveIntegerField(default=0, verbose_name="Всего визитов")
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Сумма покупок")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return f"{self.name} ({self.phone})"
    
    def get_activity_status(self):
        """Возвращает статус активности клиента"""
        from apps.schedules.models import Booking
        
        today = timezone.now().date()
        
        # Проверяем записи за последние 30 дней
        recent_bookings = Booking.objects.filter(
            client=self,
            date__gte=today - timedelta(days=30)
        ).count()
        
        # Проверяем записи за последние 90 дней
        recent_3months = Booking.objects.filter(
            client=self,
            date__gte=today - timedelta(days=90)
        ).count()
        
        # Проверяем, новый ли клиент (создан менее 30 дней назад)
        is_new = (today - self.created_at.date()).days <= 30
        
        if recent_bookings > 0:
            return "Активный"
        elif recent_3months > 0:
            return "Недавний"
        elif is_new and self.total_visits == 0:
            return "Новый"
        else:
            return "Неактивный"
    
    def get_average_check(self):
        """Возвращает средний чек клиента"""
        from apps.schedules.models import Booking
        
        if self.total_visits == 0:
            return 0
        
        avg_check = Booking.objects.filter(client=self).aggregate(
            avg_price=Avg('price')
        )['avg_price']
        
        return float(avg_check) if avg_check else 0
    
    def get_next_visit(self):
        """Возвращает дату следующего визита клиента"""
        from apps.schedules.models import Booking
        from django.utils import timezone
        
        # Получаем будущие записи
        today = timezone.now().date()
        next_booking = Booking.objects.filter(
            client=self, 
            date__gte=today
        ).order_by('date', 'start_time').first()
        
        return next_booking.date if next_booking else None
    
    def get_upcoming_bookings(self):
        """Возвращает список предстоящих записей клиента"""
        from apps.schedules.models import Booking
        from django.utils import timezone
        
        today = timezone.now().date()
        return Booking.objects.filter(
            client=self, 
            date__gte=today
        ).order_by('date', 'start_time')
    
    def get_past_bookings(self):
        """Возвращает список прошлых записей клиента"""
        from apps.schedules.models import Booking
        from django.utils import timezone
        
        today = timezone.now().date()
        return Booking.objects.filter(
            client=self, 
            date__lt=today
        ).order_by('-date', '-start_time')
