from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import requests
from .models import Booking
from apps.notifications.models import Notification
from apps.settings.models import UserNotificationSettings, BusinessNotificationSettings

def send_whatsapp_notification(phone, message):
    """Отправка уведомления через WhatsApp"""
    try:
        # Форматируем номер телефона для WhatsApp
        clean_phone = phone.replace(' ', '').replace('+', '')
        if clean_phone.startswith('996'):
            clean_phone = clean_phone[3:]
        
        if len(clean_phone) != 9:
            return False
            
        # Отправляем через WhatsApp API
        whatsapp_url = "http://localhost:3000/send"
        payload = {
            "number": f"996{clean_phone}",
            "message": message
        }
        
        response = requests.post(whatsapp_url, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

@receiver(post_save, sender=Booking)
def booking_created_notification(sender, instance, created, **kwargs):
    """Уведомление при создании новой записи"""
    if created:
        # Создаем уведомление в системе
        try:
            business = instance.service.business
            business_settings, _ = BusinessNotificationSettings.objects.get_or_create(business=business)
            
            if business_settings.whatsapp_notifications:
                # Формируем сообщение для клиента
                client_message = f"Здравствуйте, {instance.client.name}!\n\n" \
                               f"Ваша запись подтверждена:\n" \
                               f"📅 {instance.date.strftime('%d.%m.%Y')}\n" \
                               f"⏰ {instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')}\n" \
                               f"💇‍♀️ {instance.service.name}\n" \
                               f"👩‍💼 Мастер: {instance.master.name}\n\n" \
                               f"Стоимость: {instance.price} сом\n\n" \
                               f"Ждем вас!"
                
                # Отправляем клиенту
                if instance.client.phone:
                    send_whatsapp_notification(instance.client.phone, client_message)
                
                # Уведомление для мастера
                master_message = f"Новая запись:\n" \
                               f"👤 {instance.client.name}\n" \
                               f"📅 {instance.date.strftime('%d.%m.%Y')}\n" \
                               f"⏰ {instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')}\n" \
                               f"💇‍♀️ {instance.service.name}\n" \
                               f"💰 {instance.price} сом"
                
                if instance.master.phone:
                    send_whatsapp_notification(instance.master.phone, master_message)
                    
        except Exception as e:
            print(f"Ошибка отправки уведомления о записи: {e}")

@receiver(post_save, sender=Booking)
def booking_updated_notification(sender, instance, created, **kwargs):
    """Уведомление при изменении записи"""
    if not created:  # Только при изменении существующей записи
        try:
            business = instance.service.business
            business_settings, _ = BusinessNotificationSettings.objects.get_or_create(business=business)
            
            if business_settings.whatsapp_notifications:
                # Уведомление клиенту об изменении
                client_message = f"Здравствуйте, {instance.client.name}!\n\n" \
                               f"Ваша запись была изменена:\n" \
                               f"📅 {instance.date.strftime('%d.%m.%Y')}\n" \
                               f"⏰ {instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')}\n" \
                               f"💇‍♀️ {instance.service.name}\n" \
                               f"👩‍💼 Мастер: {instance.master.name}\n\n" \
                               f"Стоимость: {instance.price} сом"
                
                if instance.client.phone:
                    send_whatsapp_notification(instance.client.phone, client_message)
                    
        except Exception as e:
            print(f"Ошибка отправки уведомления об изменении записи: {e}")

@receiver(post_delete, sender=Booking)
def booking_cancelled_notification(sender, instance, **kwargs):
    """Уведомление при отмене записи"""
    try:
        business = instance.service.business
        business_settings, _ = BusinessNotificationSettings.objects.get_or_create(business=business)
        
        if business_settings.whatsapp_notifications:
            # Уведомление клиенту об отмене
            client_message = f"Здравствуйте, {instance.client.name}!\n\n" \
                           f"Ваша запись была отменена:\n" \
                           f"📅 {instance.date.strftime('%d.%m.%Y')}\n" \
                           f"⏰ {instance.start_time.strftime('%H:%M')} - {instance.end_time.strftime('%H:%M')}\n" \
                           f"💇‍♀️ {instance.service.name}\n\n" \
                           f"Для новой записи свяжитесь с нами."
            
            if instance.client.phone:
                send_whatsapp_notification(instance.client.phone, client_message)
                
    except Exception as e:
        print(f"Ошибка отправки уведомления об отмене записи: {e}")

def send_reminder_notifications():
    """Отправка напоминаний о предстоящих записях"""
    try:
        now = timezone.now()
        current_date = now.date()
        current_time = now.time()
        
        # Находим записи на сегодня и завтра
        today_bookings = Booking.objects.filter(date=current_date)
        tomorrow_bookings = Booking.objects.filter(date=current_date + timedelta(days=1))
        
        # Напоминания за 2 часа до визита (сегодня)
        for booking in today_bookings:
            try:
                # Вычисляем время за 2 часа до начала записи
                booking_datetime = timezone.make_aware(
                    timezone.datetime.combine(booking.date, booking.start_time)
                )
                reminder_time = booking_datetime - timedelta(hours=2)
                
                # Проверяем, нужно ли отправить напоминание сейчас
                if now >= reminder_time and now < reminder_time + timedelta(minutes=5):
                    business = booking.service.business
                    business_settings, _ = BusinessNotificationSettings.objects.get_or_create(business=business)
                    
                    if business_settings.whatsapp_notifications:
                        # Напоминание за 2 часа
                        reminder_message = f"Здравствуйте, {booking.client.name}!\n\n" \
                                         f"⏰ Напоминаем: через 2 часа у вас запись:\n" \
                                         f"📅 {booking.date.strftime('%d.%m.%Y')}\n" \
                                         f"🕐 {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}\n" \
                                         f"💇‍♀️ {booking.service.name}\n" \
                                         f"👩‍💼 Мастер: {booking.master.name}\n\n" \
                                         f"Не забудьте про запись! 👋"
                        
                        if booking.client.phone:
                            success = send_whatsapp_notification(booking.client.phone, reminder_message)
                            if success:
                                print(f"✅ Напоминание за 2 часа отправлено: {booking.client.name} - {booking.date} {booking.start_time}")
                            else:
                                print(f"❌ Ошибка отправки напоминания за 2 часа: {booking.client.name}")
                                
            except Exception as e:
                print(f"Ошибка отправки напоминания за 2 часа для записи {booking.id}: {e}")
        
        # Напоминания за день (завтра)
        for booking in tomorrow_bookings:
            try:
                business = booking.service.business
                business_settings, _ = BusinessNotificationSettings.objects.get_or_create(business=business)
                
                if business_settings.whatsapp_notifications:
                    # Напоминание за день
                    reminder_message = f"Здравствуйте, {booking.client.name}!\n\n" \
                                     f"📅 Напоминаем о завтрашней записи:\n" \
                                     f"📅 {booking.date.strftime('%d.%m.%Y')}\n" \
                                     f"⏰ {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}\n" \
                                     f"💇‍♀️ {booking.service.name}\n" \
                                     f"👩‍💼 Мастер: {booking.master.name}\n\n" \
                                     f"Ждем вас! 👋"
                    
                    if booking.client.phone:
                        success = send_whatsapp_notification(booking.client.phone, reminder_message)
                        if success:
                            print(f"✅ Напоминание за день отправлено: {booking.client.name} - {booking.date} {booking.start_time}")
                        else:
                            print(f"❌ Ошибка отправки напоминания за день: {booking.client.name}")
                            
            except Exception as e:
                print(f"Ошибка отправки напоминания за день для записи {booking.id}: {e}")
                
    except Exception as e:
        print(f"Ошибка отправки напоминаний: {e}")

def send_custom_reminder(booking_id, hours_before):
    """Отправка кастомного напоминания"""
    try:
        booking = Booking.objects.get(id=booking_id)
        business = booking.service.business
        business_settings, _ = BusinessNotificationSettings.objects.get_or_create(business=business)
        
        if business_settings.whatsapp_notifications and booking.client.phone:
            # Формируем сообщение в зависимости от времени
            if hours_before == 24:
                time_text = "завтра"
                emoji = "📅"
            elif hours_before == 2:
                time_text = f"через {hours_before} часа"
                emoji = "⏰"
            else:
                time_text = f"через {hours_before} часов"
                emoji = "⏰"
            
            reminder_message = f"Здравствуйте, {booking.client.name}!\n\n" \
                             f"{emoji} Напоминаем о записи {time_text}:\n" \
                             f"📅 {booking.date.strftime('%d.%m.%Y')}\n" \
                             f"⏰ {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}\n" \
                             f"💇‍♀️ {booking.service.name}\n" \
                             f"👩‍💼 Мастер: {booking.master.name}\n\n" \
                             f"Ждем вас! 👋"
            
            success = send_whatsapp_notification(booking.client.phone, reminder_message)
            return success
        else:
            return False
            
    except Exception as e:
        print(f"Ошибка отправки кастомного напоминания: {e}")
        return False 