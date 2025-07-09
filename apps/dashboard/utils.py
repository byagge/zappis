import g4f
import json
from typing import List, Dict, Any
from apps.businesses.models import Business
from apps.dashboard.models import FinanceRecord, ActivityLog, AIAdvice
from apps.accounts.models import User
from django.utils import timezone
from django.db.models import Sum, Avg
from datetime import timedelta
import traceback
import threading
from django.db import close_old_connections
from apps.clients.models import Client
from apps.employees.models import Employee
from apps.schedules.models import Booking
from apps.services.models import Service
try:
    from apps.settings.models import Settings
except ImportError:
    Settings = None

# --- G4F AI CLIENT ---
try:
    from g4f.client import Client as G4FClient
except ImportError:
    from pip._internal.cli.main import main
    main(["install", "-U", "g4f"])
    from g4f.client import Client as G4FClient
client = G4FClient()

G4F_MODEL = "gpt-4o"
G4F_ATTEMPTS = 3


def generate_ai_advices(business: Business, extra_context: str = "", lang: str = "ru") -> List[Dict[str, Any]]:
    """
    Генерирует короткие ИИ-советы для бизнеса на основе всех реальных данных через g4f
    extra_context: дополнительная строка с уникальными особенностями бизнеса
    lang: язык генерации ('ru' или 'ky')
    """
    print(f"=== DEBUG: Начинаем генерацию ИИ-советов для бизнеса {business.name} ===")
    try:
        # Собираем все данные по бизнесу
        print("DEBUG: Собираем все данные по бизнесу...")
        business_data = {
            "id": business.id,
            "name": business.name,
            "type": str(getattr(business.type, 'name', '')),
            # Добавьте другие нужные поля
        }
        users = list(User.objects.filter(business=business).values())
        clients = list(Client.objects.filter(business=business).values())
        employees = list(Employee.objects.filter(business=business).values())
        bookings = list(Booking.objects.filter(service__business=business).values())
        services = list(Service.objects.filter(business=business).values())
        settings = list(Settings.objects.filter(business=business).values()) if Settings else []

        all_data = {
            "business": business_data,
            "users": users,
            "clients": clients,
            "employees": employees,
            "bookings": bookings,
            "services": services,
            "settings": settings,
            "extra_context": extra_context,
        }
        context = json.dumps(all_data, ensure_ascii=False, default=str)[:12000]  # Ограничить размер prompt
        print(f"DEBUG: Контекст для ИИ (JSON):\n{context}")
        if lang == "ky":
            prompt = f"""
            Сен — чакан бизнести өнүктүрүү боюнча экспертсиң. Бул бизнес тууралуу бардык маалыматтар JSON форматында:
            {context}
            Ушул маалыматтардын негизинде кирешени көбөйтүү жана кардарларды кармап калуу үчүн 3 жеке, так кеңеш бер. Ар бир кеңеш 1-2 сүйлөм, 70 символдон ашпасын. Жалпы сөздөрдү колдонбо. Жооп форматы — JSON массив:
            [
                {{
                    "title": "Кыскача аталыш (50 символго чейин)",
                    "description": "Кыскача сүрөттөмө (70 символго чейин)",
                    "icon": "trending-up",
                    "priority": 1
                }}
            ]
            Иконкалар: trending-up, users, dollar-sign, lightbulb, clock, star
            Приоритет: 1 (маанилүү), 2 (орточо), 3 (шашылыш эмес)
            """
        else:
            prompt = f"""
            Ты — эксперт по развитию малого бизнеса. Вот все данные бизнеса в JSON:
            {context}
            На основе этих данных дай 3 персонализированных, конкретных совета для роста прибыли и удержания клиентов. Каждый совет — 1-2 предложения, не длиннее 70 символов. Не используй общие фразы. Формат ответа — JSON массив:
            [
                {{
                    "title": "Короткий заголовок (до 50 символов)",
                    "description": "Краткое описание (до 70 символов)",
                    "icon": "trending-up",
                    "priority": 1
                }}
            ]
            Используй только иконки: trending-up, users, dollar-sign, lightbulb, clock, star
            Приоритет: 1 (важно), 2 (средне), 3 (не срочно)
            """
        print(f"DEBUG: Промпт для ИИ:\n{prompt}")
        # --- G4F AI GENERATION ---
        for attempt in range(G4F_ATTEMPTS):
            try:
                print(f"DEBUG: G4F попытка {attempt+1}")
                response = client.chat.completions.create(
                    model=G4F_MODEL,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.choices[0].message.content
                print(f"DEBUG: Ответ G4F:\n{content}")
                # Парсим JSON из ответа
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    advices = json.loads(json_str)
                    # Ограничиваем длину title/description
                    for advice in advices:
                        advice['title'] = advice.get('title', '')[:50]
                        desc = advice.get('description', '')[:70]
                        if not desc.endswith('.'):
                            desc = desc.rstrip() + '.'
                        advice['description'] = desc
                    if isinstance(advices, list) and len(advices) > 0:
                        print(f"DEBUG: Успешно получены {len(advices)} советов")
                        return advices
                    else:
                        print(f"DEBUG: Неверный формат ответа ИИ: {type(advices)}, длина: {len(advices) if isinstance(advices, list) else 'N/A'}")
                        continue
                else:
                    print(f"DEBUG: JSON не найден в ответе. start_idx: {start_idx}, end_idx: {end_idx}")
                    continue
            except Exception as e:
                print(f"DEBUG: Ошибка G4F: {e}")
                print(f"DEBUG: Traceback:\n{traceback.format_exc()}")
                continue
        print("DEBUG: Все попытки G4F не дали валидного результата")
        return []
    except Exception as e:
        print(f"DEBUG: Общая ошибка генерации ИИ-советов: {e}")
        print(f"DEBUG: Traceback:\n{traceback.format_exc()}")
        return []


def get_or_update_ai_advices(business: Business, force_update: bool = False, extra_context: str = "", lang: str = "ru") -> List[Dict[str, Any]]:
    """
    Возвращает советы из AIAdvice, если они не устарели, иначе генерирует новые, сохраняет и возвращает их.
    force_update — если True, советы будут сгенерированы заново.
    extra_context — строка с уникальными особенностями бизнеса для персонализации.
    lang — язык генерации ('ru' или 'ky')
    """
    try:
        advice_obj = AIAdvice.objects.filter(business=business).first()
        if advice_obj and not advice_obj.is_outdated() and not force_update:
            print(f"DEBUG: Используем свежие советы из БД для {business.name}")
            return advice_obj.data
        print(f"DEBUG: Генерируем новые советы для {business.name}")
        advices = generate_ai_advices(business, extra_context=extra_context, lang=lang)
        if advices:
            if advice_obj:
                advice_obj.data = advices
                advice_obj.save(update_fields=["data", "updated_at"])
            else:
                AIAdvice.objects.create(business=business, data=advices)
            return advices
        else:
            print("DEBUG: Не удалось сгенерировать советы, возвращаем старые или сообщение о недоступности")
            if advice_obj:
                return advice_obj.data
            return create_unavailable_message(lang=lang)
    except Exception as e:
        print(f"DEBUG: Ошибка при получении/обновлении советов: {e}")
        print(f"DEBUG: Traceback:\n{traceback.format_exc()}")
        return create_unavailable_message(lang=lang)

def create_unavailable_message(lang: str = "ru") -> List[Dict[str, Any]]:
    """Возвращает сообщение о недоступности ИИ-советов"""
    print("DEBUG: Создаем сообщение о недоступности ИИ-советов")
    if lang == "ky":
        return [
            {
                "title": "AI кеңештер убактылуу жеткиликсиз",
                "description": "AI кеңештер сервиси учурда жеткиликсиз. Кийинчерээк аракет кылыңыз.",
                "icon": "alert-circle",
                "priority": 1
            }
        ]
    return [
        {
            "title": "ИИ-советы временно недоступны",
            "description": "В данный момент сервис ИИ-советов недоступен. Попробуйте обновить позже.",
            "icon": "alert-circle",
            "priority": 1
        }
    ]

def _background_generate_and_save_ai_advices(business, extra_context="", lang="ru"):
    close_old_connections()
    advices = generate_ai_advices(business, extra_context=extra_context, lang=lang)
    if advices:
        obj, created = AIAdvice.objects.get_or_create(business=business, defaults={'data': advices})
        if not created:
            obj.data = advices
            obj.save(update_fields=["data", "updated_at"])


def get_ai_advices_from_db_or_trigger_bg(business, extra_context="", lang="ru"):
    """
    Возвращает {'pending': True, 'advices': []} если советов нет, иначе {'pending': False, 'advices': [...]}.
    Если советов нет или они устарели — запускает фоновую генерацию.
    lang — язык генерации ('ru' или 'ky')
    """
    from .models import AIAdvice
    advice_obj = AIAdvice.objects.filter(business=business).first()
    if advice_obj and not advice_obj.is_outdated():
        return {'pending': False, 'advices': advice_obj.data}
    # Если советов нет или устарели — запускаем фоновую генерацию
    threading.Thread(target=_background_generate_and_save_ai_advices, args=(business, extra_context, lang), daemon=True).start()
    if advice_obj:
        return {'pending': False, 'advices': advice_obj.data}
    return {'pending': True, 'advices': []} 