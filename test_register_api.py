#!/usr/bin/env python
import requests
import json

def get_business_types():
    """Получает типы бизнеса из API"""
    url = "http://localhost:8000/accounts/api/business-types/"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('business_types', [])
        else:
            print(f"❌ Ошибка получения типов бизнеса: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Ошибка подключения к API типов бизнеса: {e}")
        return []

def test_register_api():
    """Тестирует API регистрации"""
    
    # Получаем типы бизнеса
    print("📋 Получение типов бизнеса...")
    business_types = get_business_types()
    
    if not business_types:
        print("❌ Не удалось получить типы бизнеса. Используем значение по умолчанию.")
        business_type_id = "1"
    else:
        print("✅ Типы бизнеса получены:")
        for bt in business_types:
            print(f"  {bt['id']}: {bt['name']}")
        business_type_id = str(business_types[0]['id'])
    
    # URL API
    url = "http://localhost:8000/accounts/api/register/"
    
    # Тестовые данные
    test_data = {
        "full_name": "Тест Тестов",
        "phone": "999123456",
        "company_name": "Тестовая компания",
        "business_type": business_type_id,
        "password": "testpass123",
        "agree_to_terms": True
    }
    
    # Заголовки
    headers = {
        "Content-Type": "application/json",
    }
    
    try:
        print("\n🚀 Тестирование API регистрации...")
        print(f"📡 URL: {url}")
        print(f"📦 Данные: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        # Отправляем запрос
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"\n📊 Статус ответа: {response.status_code}")
        print(f"📋 Заголовки ответа: {dict(response.headers)}")
        
        # Пытаемся получить JSON ответ
        try:
            response_data = response.json()
            print(f"📄 Ответ JSON: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print(f"📄 Ответ (не JSON): {response.text}")
        
        # Анализируем результат
        if response.status_code == 201:
            print("\n✅ УСПЕХ! Регистрация прошла успешно!")
            if 'token' in response_data:
                print(f"🔑 Получен токен: {response_data['token'][:50]}...")
            if 'user' in response_data:
                print(f"👤 Пользователь: {response_data['user']['full_name']}")
        elif response.status_code == 400:
            print("\n❌ ОШИБКА ВАЛИДАЦИИ!")
            if 'detail' in response_data:
                print(f"💬 Сообщение: {response_data['detail']}")
        else:
            print(f"\n❌ НЕОЖИДАННАЯ ОШИБКА! Статус: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ОШИБКА ПОДКЛЮЧЕНИЯ!")
        print("Убедитесь, что сервер Django запущен на http://localhost:8000")
    except Exception as e:
        print(f"❌ ОШИБКА: {str(e)}")

if __name__ == "__main__":
    test_register_api() 