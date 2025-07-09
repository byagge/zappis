from django.db import models
from django.conf import settings
from apps.businesses.models import Business
 
# Create your models here. 

class UserNotificationSettings(models.Model):
    """Настройки уведомлений пользователя"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name='Пользователь'
    )
    email_notifications = models.BooleanField(default=False, verbose_name='Уведомления по Email')
    sms_notifications = models.BooleanField(default=False, verbose_name='SMS уведомления')
    whatsapp_notifications = models.BooleanField(default=False, verbose_name='Уведомления WhatsApp')
    telegram_notifications = models.BooleanField(default=True, verbose_name='Уведомления Telegram')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Настройки уведомлений пользователя'
        verbose_name_plural = 'Настройки уведомлений пользователей'

    def __str__(self):
        return f"Настройки уведомлений для {self.user.full_name}"

class BusinessNotificationSettings(models.Model):
    """Настройки уведомлений бизнеса"""
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name='Бизнес'
    )
    email_notifications = models.BooleanField(default=False, verbose_name='Уведомления по Email')
    sms_notifications = models.BooleanField(default=False, verbose_name='SMS уведомления')
    whatsapp_notifications = models.BooleanField(default=False, verbose_name='Уведомления WhatsApp')
    telegram_notifications = models.BooleanField(default=True, verbose_name='Уведомления Telegram')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Настройки уведомлений бизнеса'
        verbose_name_plural = 'Настройки уведомлений бизнесов'

    def __str__(self):
        return f"Настройки уведомлений для {self.business.name}"

class BookingSettings(models.Model):
    """Настройки бронирования для бизнеса"""
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name='booking_settings',
        verbose_name='Бизнес'
    )
    default_slot_duration = models.IntegerField(
        default=60,
        choices=[
            (15, '15 минут'),
            (30, '30 минут'),
            (45, '45 минут'),
            (60, '60 минут'),
        ],
        verbose_name='Длительность слота по умолчанию (минуты)'
    )
    buffer_time = models.IntegerField(
        default=0,
        choices=[
            (0, 'Без буфера'),
            (5, '5 минут'),
            (10, '10 минут'),
            (15, '15 минут'),
        ],
        verbose_name='Буферное время (минуты)'
    )
    auto_confirm_bookings = models.BooleanField(
        default=True,
        verbose_name='Автоматическое подтверждение бронирований'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Настройки бронирования'
        verbose_name_plural = 'Настройки бронирования'

    def __str__(self):
        return f"Настройки бронирования для {self.business.name}"

class UserPreferences(models.Model):
    """Дополнительные настройки пользователя"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name='Пользователь'
    )
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Светлая'),
            ('dark', 'Темная'),
            ('auto', 'Авто'),
        ],
        default='light',
        verbose_name='Тема оформления'
    )
    language = models.CharField(
        max_length=10,
        choices=[
            ('ru', 'Русский'),
            ('en', 'English'),
            ('ky', 'Кыргызча'),
        ],
        default='ru',
        verbose_name='Язык интерфейса'
    )
    timezone = models.CharField(
        max_length=50,
        default='Asia/Bishkek',
        verbose_name='Часовой пояс'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Настройки пользователя'
        verbose_name_plural = 'Настройки пользователей'

    def __str__(self):
        return f"Настройки для {self.user.full_name}" 