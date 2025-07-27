# API Регистрации Zappis

## 📋 Описание

Создан простой API для регистрации пользователей в системе Zappis. API принимает данные формы регистрации и создает пользователя с бизнесом.

## 🚀 Настройка

### 1. Создание типов бизнеса

Перед использованием API необходимо создать типы бизнеса в базе данных:

```bash
python create_business_types.py
```

Этот скрипт создаст следующие типы бизнеса:
- Салон красоты
- Медицина
- Фитнес
- Образование
- Другое

### 2. Запуск сервера

```bash
python manage.py runserver
```

## 🔧 API Endpoints

### GET /accounts/api/business-types/

Получает список всех типов бизнеса.

**Успешный ответ (200):**
```json
{
    "business_types": [
        {"id": 1, "name": "Салон красоты"},
        {"id": 2, "name": "Медицина"},
        {"id": 3, "name": "Фитнес"},
        {"id": 4, "name": "Образование"},
        {"id": 5, "name": "Другое"}
    ]
}
```

### POST /accounts/api/register/

Регистрирует нового пользователя и создает бизнес.

**Параметры:**
- `full_name` (string, обязательный) - ФИО пользователя
- `phone` (string, обязательный) - Номер телефона (9 цифр без кода страны)
- `company_name` (string, обязательный) - Название компании
- `business_type` (string, обязательный) - ID типа бизнеса
- `password` (string, обязательный) - Пароль (минимум 6 символов)
- `agree_to_terms` (boolean, обязательный) - Согласие с условиями

**Пример запроса:**
```json
{
    "full_name": "Иван Иванов",
    "phone": "999123456",
    "company_name": "Салон красоты 'Красота'",
    "business_type": "1",
    "password": "mypassword123",
    "agree_to_terms": true
}
```

**Успешный ответ (201):**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": "uuid-here",
        "full_name": "Иван Иванов",
        "phone_number": "+996999123456",
        "business": {
            "id": 1,
            "name": "Салон красоты 'Красота'"
        }
    },
    "message": "Регистрация успешно завершена"
}
```

**Ошибка валидации (400):**
```json
{
    "detail": "Все поля обязательны для заполнения"
}
```

## 🧪 Тестирование

### Автоматический тест

Запустите тестовый скрипт:

```bash
python test_register_api.py
```

### Ручное тестирование

1. Откройте страницу регистрации: `http://localhost:8000/accounts/register/`
2. Заполните форму
3. Нажмите "Создать аккаунт"
4. Проверьте результат

### Тестирование через curl

**Получение типов бизнеса:**
```bash
curl -X GET http://localhost:8000/accounts/api/business-types/
```

**Регистрация пользователя:**
```bash
curl -X POST http://localhost:8000/accounts/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Тест Тестов",
    "phone": "999123456",
    "company_name": "Тестовая компания",
    "business_type": "1",
    "password": "testpass123",
    "agree_to_terms": true
  }'
```

## 🔍 Отладка

### Проверка логов Django

```bash
python manage.py runserver --verbosity=2
```

### Проверка базы данных

```bash
python manage.py shell
```

```python
from apps.accounts.models import User
from apps.businesses.models import Business, BusinessType

# Проверить пользователей
User.objects.all().values('full_name', 'phone_number')

# Проверить бизнесы
Business.objects.all().values('name', 'type__name', 'owner__full_name')

# Проверить типы бизнеса
BusinessType.objects.all().values('id', 'name')
```

## ⚠️ Важные моменты

1. **Телефон**: API автоматически добавляет код страны +996
2. **Город**: По умолчанию используется первый город из Кыргызстана
3. **Роль**: Все зарегистрированные пользователи получают роль ADMIN
4. **Верификация**: Пока отключена (is_phone_verified=True)
5. **Бизнес**: Автоматически создается и связывается с пользователем
6. **Типы бизнеса**: Загружаются из базы данных, а не захардкожены

## 🐛 Известные проблемы

- Если нет городов в базе данных, регистрация не пройдет
- Если нет типов бизнеса, нужно запустить `create_business_types.py`
- Проблемы с зависимостями Wagtail могут помешать запуску Django shell

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи Django
2. Убедитесь, что все миграции применены
3. Проверьте наличие данных в базе
4. Запустите тестовый скрипт для диагностики 