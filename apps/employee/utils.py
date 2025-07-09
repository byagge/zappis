import json
from typing import List, Dict, Any
from apps.schedules.models import Booking
from apps.clients.models import Client
from apps.employees.models import Employee
from apps.employee.models import EmployeeAIAdvice
from django.db.models import Sum, Avg
import traceback

# --- G4F AI CLIENT ---
try:
    from g4f.client import Client as G4FClient
except ImportError:
    G4FClient = None
client = G4FClient() if G4FClient else None
G4F_MODEL = "gpt-4o"
G4F_ATTEMPTS = 3

def generate_employee_ai_advices(employee: Employee, save_to_db=True) -> List[Dict[str, Any]]:
    """
    Генерирует короткие ИИ-советы для сотрудника на основе его клиентов и записей
    Если save_to_db=True, сохраняет советы в EmployeeAIAdvice
    """
    try:
        # Собираем данные по сотруднику
        bookings = list(Booking.objects.filter(master=employee).values())
        clients = list(Client.objects.filter(bookings__master=employee).distinct().values())
        all_data = {
            "employee": {
                "id": employee.id,
                "name": employee.name,
                "position": str(employee.position),
                "is_master": employee.is_master,
            },
            "clients": clients,
            "bookings": bookings,
        }
        context = json.dumps(all_data, ensure_ascii=False, default=str)[:12000]
        prompt = f"""
        Ты — эксперт по развитию мастеров сферы услуг. Вот все данные сотрудника в JSON:
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
        for attempt in range(G4F_ATTEMPTS):
            try:
                if not client:
                    return create_unavailable_message()
                response = client.chat.completions.create(
                    model=G4F_MODEL,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.choices[0].message.content
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    advices = json.loads(json_str)
                    for advice in advices:
                        advice['title'] = advice.get('title', '')[:50]
                        desc = advice.get('description', '')[:70]
                        if not desc.endswith('.'):
                            desc = desc.rstrip() + '.'
                        advice['description'] = desc
                    if isinstance(advices, list) and len(advices) > 0:
                        if save_to_db:
                            EmployeeAIAdvice.objects.filter(employee=employee).delete()
                            for advice in advices:
                                EmployeeAIAdvice.objects.create(
                                    employee=employee,
                                    title=advice['title'],
                                    description=advice['description'],
                                    icon=advice.get('icon', 'bot'),
                                    priority=advice.get('priority', 1)
                                )
                        return advices
                    continue
            except Exception as e:
                continue
        return create_unavailable_message()
    except Exception as e:
        return create_unavailable_message()

def create_unavailable_message() -> List[Dict[str, Any]]:
    return [
        {
            "title": "ИИ-советы временно недоступны",
            "description": "В данный момент сервис ИИ-советов недоступен. Попробуйте позже.",
            "icon": "alert-circle",
            "priority": 1
        }
    ]

def _background_generate_and_save_employee_ai_advices(employee):
    generate_employee_ai_advices(employee)

def get_employee_ai_advices_from_db_or_trigger_bg(employee, force_update=False):
    # Если force_update — всегда пересоздаём советы
    if force_update:
        advices = generate_employee_ai_advices(employee, save_to_db=True)
        return {'pending': False, 'advices': advices}
    # Иначе ищем советы в БД
    advices_qs = EmployeeAIAdvice.objects.filter(employee=employee).order_by('priority', '-created_at')
    if advices_qs.exists():
        advices = [
            {
                'title': a.title,
                'description': a.description,
                'icon': a.icon,
                'priority': a.priority
            } for a in advices_qs
        ]
        return {'pending': False, 'advices': advices}
    # Если нет — генерируем и сохраняем
    advices = generate_employee_ai_advices(employee, save_to_db=True)
    return {'pending': False, 'advices': advices} 