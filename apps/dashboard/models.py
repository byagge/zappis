from django.db import models
from django.conf import settings
from apps.businesses.models import Business
from django.utils import timezone

# Create your models here.

class BusinessStats(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='stats')
    total_clients = models.PositiveIntegerField(default=0)
    total_appointments = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_ticket = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Статистика для {self.business.name}"

class FinanceRecord(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='finance_records')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255, blank=True)
    is_income = models.BooleanField(default=True)

    def __str__(self):
        return f"{'Доход' if self.is_income else 'Расход'}: {self.amount} ({self.business.name})"

class ActivityLog(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    extra = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} ({self.business.name})"

class AIAdvice(models.Model):
    """Модель для хранения ИИ-советов с автоматическим обновлением"""
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='ai_advices')
    data = models.JSONField(help_text="Список советов в формате JSON")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['business']

    def __str__(self):
        return f"ИИ-советы для {self.business.name}"

    def is_outdated(self):
        """Проверяет, устарели ли советы (старше 7 дней)"""
        return (timezone.now() - self.updated_at).days >= 7
