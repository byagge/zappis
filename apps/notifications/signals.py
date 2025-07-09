from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Notification

# Пример: уведомление при создании нового пользователя
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def user_created_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance,
            type='system',
            title='Добро пожаловать!',
            message='Ваш аккаунт успешно создан.',
            date=instance.date_joined if hasattr(instance, 'date_joined') else None,
            is_important=True
        ) 