from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from apps.accounts.models import User
from apps.businesses.models import Business
from .models import UserNotificationSettings, BusinessNotificationSettings, BookingSettings, UserPreferences

@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Автоматически создает настройки для нового пользователя"""
    if created:
        UserNotificationSettings.objects.create(user=instance)
        UserPreferences.objects.create(user=instance)

@receiver(post_save, sender=Business)
def create_business_settings(sender, instance, created, **kwargs):
    """Автоматически создает настройки для нового бизнеса"""
    if created:
        BusinessNotificationSettings.objects.create(business=instance)
        BookingSettings.objects.create(business=instance)

# from django.db.models.signals import ...
# from django.dispatch import receiver
# from .models import ...
 
# @receiver(...)
# def ..._handler(sender, instance, created, **kwargs):
#     pass 