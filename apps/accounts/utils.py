import random
import requests
from .models import RegistrationSession

def send_sms(phone: str) -> str:
    code = f"{random.randint(0, 999999):06d}"
    # Найти последнюю сессию регистрации по номеру телефона
    session = RegistrationSession.objects.filter(phone=phone).order_by('-created_at').first()
    if session:
        session.code = code
        session.save()
    
    # Отправляем код через WhatsApp
    try:
        # Форматируем номер телефона для WhatsApp (убираем + и добавляем код страны если нужно)
        whatsapp_number = phone.replace('+', '')
        if not whatsapp_number.startswith('996'):
            whatsapp_number = '996' + whatsapp_number
        
        # Формируем сообщение
        message = f"🔐 Ваш код подтверждения для регистрации в Zappis: {code}\n\nКод действителен в течение 10 минут."
        
        # Отправляем через WhatsApp API
        response = requests.post(
            'http://localhost:3000/send',
            json={
                'number': whatsapp_number,
                'message': message
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ WhatsApp код отправлен на {phone}: {code}")
        else:
            print(f"❌ Ошибка отправки WhatsApp на {phone}: {response.text}")
            # Fallback: выводим код в консоль для тестирования
            print(f"Ваш код для {phone}: {code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к WhatsApp API: {e}")
        # Fallback: выводим код в консоль для тестирования
        print(f"Ваш код для {phone}: {code}")
    
    return code
