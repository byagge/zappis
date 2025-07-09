from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg
from django.views.generic import TemplateView
from apps.clients.models import Client
from apps.schedules.models import Booking
from apps.employees.models import Employee
from apps.services.models import Service
from .serializers import (
    EmployeeDashboardOverviewSerializer,
    EmployeeRevenueChartSerializer,
    EmployeeAIInsightSerializer,
    EmployeeTopClientSerializer,
)
from .utils import generate_employee_ai_advices, get_employee_ai_advices_from_db_or_trigger_bg
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from apps.clients.serializers import ClientSerializer
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from apps.schedules.serializers import BookingSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from rest_framework.permissions import BasePermission

"""
ViewSet'ы для личного кабинета сотрудника:
- Dashboard
- Schedules
- Notifications
- Clients

Доступ: админ — всё, сотрудник — только свои данные.
"""

# Create your views here.

def is_mobile(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()
    return any(x in ua for x in ['iphone', 'android', 'ipad', 'mobile', 'opera mini', 'blackberry', 'webos'])

def get_user_language(request):
    """
    Определяет язык пользователя: ?lang=, user.preferred_language, session, Accept-Language. Только 'ru' или 'ky'.
    Если lang передан в GET, сохраняет в user и session.
    """
    user = getattr(request, 'user', None)
    lang_param = request.GET.get('lang')
    lang = None
    if lang_param in ['ru', 'ky']:
        lang = lang_param
        # Сохраняем выбор пользователя
        if user and user.is_authenticated and hasattr(user, 'preferred_language') and getattr(user, 'preferred_language', None) != lang_param:
            user.preferred_language = lang_param
            user.save(update_fields=["preferred_language"])
        request.session['preferred_language'] = lang_param
    if not lang and user and user.is_authenticated:
        lang = getattr(user, 'preferred_language', None)
    if not lang:
        lang = request.session.get('preferred_language')
    if not lang:
        accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '').lower()
        if accept_lang.startswith('ky'):
            lang = 'ky'
        elif accept_lang.startswith('ru'):
            lang = 'ru'
    if lang not in ['ru', 'ky']:
        lang = 'ru'
    return lang

def employee_only_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or not hasattr(user, 'employee') or not user.employee.is_master:
            if user.is_authenticated and (user.is_superuser or user.is_staff):
                return HttpResponseRedirect('/dashboard/')
            return HttpResponseRedirect('/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

class EmployeeDashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if not hasattr(user, 'employee') or not user.employee.is_master:
            return Response({'error': 'Нет доступа'}, status=403)
        employee = user.employee
        today = timezone.now().date()
        current_month = timezone.now().month
        current_year = timezone.now().year
        total_clients = Client.objects.filter(bookings__master=employee).distinct().count()
        appointments_today = Booking.objects.filter(master=employee, date=today).count()
        monthly_revenue = Booking.objects.filter(master=employee, date__month=current_month, date__year=current_year).aggregate(total=Sum('price'))['total'] or 0
        avg_ticket = Booking.objects.filter(master=employee).aggregate(avg=Avg('price'))['avg'] or 0
        # Рост по сравнению с прошлым месяцем
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        last_month_revenue = Booking.objects.filter(master=employee, date__month=last_month, date__year=last_month_year).aggregate(total=Sum('price'))['total'] or 0
        last_month_clients = Client.objects.filter(bookings__master=employee, bookings__date__month=last_month, bookings__date__year=last_month_year).distinct().count()
        current_month_clients = Client.objects.filter(bookings__master=employee, bookings__date__month=current_month, bookings__date__year=current_year).distinct().count()
        last_month_appointments = Booking.objects.filter(master=employee, date__month=last_month, date__year=last_month_year).count()
        current_month_appointments = Booking.objects.filter(master=employee, date__month=current_month, date__year=current_year).count()
        last_month_avg_ticket = Booking.objects.filter(master=employee, date__month=last_month, date__year=last_month_year).aggregate(avg=Avg('price'))['avg'] or 0
        revenue_growth = ((monthly_revenue - last_month_revenue) / last_month_revenue) * 100 if last_month_revenue > 0 else 0
        clients_growth = ((current_month_clients - last_month_clients) / last_month_clients) * 100 if last_month_clients > 0 else (current_month_clients * 100 if current_month_clients > 0 else 0)
        appointments_growth = ((current_month_appointments - last_month_appointments) / last_month_appointments) * 100 if last_month_appointments > 0 else (current_month_appointments * 100 if current_month_appointments > 0 else 0)
        avg_ticket_change = ((avg_ticket - last_month_avg_ticket) / last_month_avg_ticket) * 100 if last_month_avg_ticket > 0 else 0
        data = {
            'total_clients': total_clients,
            'appointments_today': appointments_today,
            'monthly_revenue': float(monthly_revenue),
            'avg_ticket': float(avg_ticket),
            'clients_growth': round(clients_growth, 1),
            'revenue_growth': round(revenue_growth, 1),
            'appointments_growth': round(appointments_growth, 1),
            'avg_ticket_change': round(avg_ticket_change, 1),
            'user_name': employee.name,
        }
        serializer = EmployeeDashboardOverviewSerializer(data)
        return Response(serializer.data)

class EmployeeRevenueChartView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if not hasattr(user, 'employee') or not user.employee.is_master:
            return Response({'error': 'Нет доступа'}, status=403)
        employee = user.employee
        period = request.GET.get('period', 'week')
        now = timezone.now().date()
        if period == 'year':
            labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
            revenue, bookings, clients = [], [], []
            for month in range(1, 13):
                revenue_val = Booking.objects.filter(master=employee, date__year=now.year, date__month=month).aggregate(total=Sum('price'))['total'] or 0
                bookings_val = Booking.objects.filter(master=employee, date__year=now.year, date__month=month).count()
                clients_val = Client.objects.filter(bookings__master=employee, bookings__date__year=now.year, bookings__date__month=month).distinct().count()
                revenue.append(float(revenue_val))
                bookings.append(bookings_val)
                clients.append(clients_val)
        elif period == 'month':
            import calendar
            days_in_month = calendar.monthrange(now.year, now.month)[1]
            labels = [str(day) for day in range(1, days_in_month + 1)]
            revenue, bookings, clients = [], [], []
            for day in range(1, days_in_month + 1):
                date = now.replace(day=day)
                revenue_val = Booking.objects.filter(master=employee, date=date).aggregate(total=Sum('price'))['total'] or 0
                bookings_val = Booking.objects.filter(master=employee, date=date).count()
                clients_val = Client.objects.filter(bookings__master=employee, bookings__date=date).distinct().count()
                revenue.append(float(revenue_val))
                bookings.append(bookings_val)
                clients.append(clients_val)
        else:
            end_date = now
            start_date = end_date - timedelta(days=6)
            dates = [end_date - timedelta(days=i) for i in range(6, -1, -1)]
            labels = [self._get_russian_day_name(date) for date in dates]
            revenue, bookings, clients = [], [], []
            for date in dates:
                revenue_val = Booking.objects.filter(master=employee, date=date).aggregate(total=Sum('price'))['total'] or 0
                bookings_val = Booking.objects.filter(master=employee, date=date).count()
                clients_val = Client.objects.filter(bookings__master=employee, bookings__date=date).distinct().count()
                revenue.append(float(revenue_val))
                bookings.append(bookings_val)
                clients.append(clients_val)
        chart_data = {
            'labels': labels,
            'revenue': revenue,
            'bookings': bookings,
            'clients': clients
        }
        serializer = EmployeeRevenueChartSerializer(chart_data)
        return Response(serializer.data)
    def _get_russian_day_name(self, date):
        day_names = {0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'}
        return day_names[date.weekday()]

class EmployeeAIInsightsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if not hasattr(user, 'employee') or not user.employee.is_master:
            return Response([], status=403)
        employee = user.employee
        force_update = request.query_params.get('force_update') == 'true'
        result = get_employee_ai_advices_from_db_or_trigger_bg(employee, force_update=force_update)
        advices = result['advices']
        serializer = EmployeeAIInsightSerializer(advices, many=True)
        return Response({'pending': False, 'advices': serializer.data})

class EmployeeTopClientsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if not hasattr(user, 'employee') or not user.employee.is_master:
            return Response({'error': 'Нет доступа'}, status=403)
        employee = user.employee
        top_clients = Client.objects.filter(bookings__master=employee).annotate(
            booking_count=Count('bookings'),
            top_total_spent=Sum('bookings__price')
        ).order_by('-top_total_spent')[:5]
        serializer = EmployeeTopClientSerializer(top_clients, many=True)
        return Response(serializer.data)

class EmployeeRecentActivityView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if not hasattr(user, 'employee') or not user.employee.is_master:
            return Response({'activities': [], 'error': 'Нет доступа'}, status=403)
        employee = user.employee
        activities = []
        recent_bookings = Booking.objects.filter(master=employee).order_by('-created_at')[:5]
        for booking in recent_bookings:
            time_ago = self._get_time_ago(booking.created_at)
            activities.append({
                'id': f'booking_{booking.id}',
                'action': f'Новая запись: {booking.service.name}',
                'time_ago': time_ago,
                'extra': {
                    'client': booking.client.name,
                    'service': booking.service.name,
                    'amount': booking.price,
                    'date': booking.date.strftime('%d.%m.%Y'),
                    'time': booking.start_time.strftime('%H:%M')
                }
            })
        recent_clients = Client.objects.filter(bookings__master=employee).order_by('-created_at')[:3]
        for client in recent_clients:
            time_ago = self._get_time_ago(client.created_at)
            activities.append({
                'id': f'client_{client.id}',
                'action': 'Новый клиент зарегистрирован',
                'time_ago': time_ago,
                'extra': {
                    'client_name': client.name,
                    'phone': client.phone,
                    'status': client.get_status_display()
                }
            })
        activities.sort(key=lambda x: x.get('time_ago', ''), reverse=True)
        activities = activities[:10]
        return Response({'activities': activities})
    def _get_time_ago(self, timestamp):
        now = timezone.now()
        diff = now - timestamp
        if diff.days > 0:
            return f"{diff.days} дней назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} часов назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} минут назад"
        else:
            return "Только что"

@csrf_exempt
@require_http_methods(["POST"])
def ai_chat(request):
    """API для AI чата сотрудника"""
    logger = logging.getLogger(__name__)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        # Получаем сообщение пользователя
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        logger.info(f"AI Chat request: {user_message}")
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Получаем сотрудника
        try:
            employee = request.user.employee
            logger.info(f"Employee found: {employee.name}")
        except Exception as e:
            logger.error(f"Employee not found: {e}")
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        # Генерируем ответ на основе сообщения и данных сотрудника
        try:
            ai_response = generate_ai_chat_response(user_message, employee)
            logger.info(f"AI response generated: {ai_response[:100]}...")
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return JsonResponse({'error': 'Failed to generate response'}, status=500)
        
        return JsonResponse({
            'response': ai_response,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in ai_chat: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

def generate_ai_chat_response(user_message: str, employee) -> str:
    """Генерирует умный ответ AI на основе сообщения пользователя и данных сотрудника"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from apps.schedules.models import Booking
        from apps.clients.models import Client
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        logger.info("Starting AI response generation")
        
        # Собираем актуальные данные сотрудника
        today = timezone.now().date()
        month_ago = timezone.now() - timedelta(days=30)
        
        logger.info(f"Date range: today={today}, month_ago={month_ago}")
        
        # Статистика по клиентам
        total_clients = Client.objects.filter(bookings__master=employee).distinct().count()
        new_clients_this_month = Client.objects.filter(
            bookings__master=employee,
            created_at__gte=month_ago
        ).distinct().count()
        
        logger.info(f"Client stats: total={total_clients}, new={new_clients_this_month}")
        
        # Статистика по записям
        appointments_today = Booking.objects.filter(
            master=employee,
            date=today
        ).count()
        
        appointments_this_month = Booking.objects.filter(
            master=employee,
            date__gte=month_ago.date()
        ).count()
        
        logger.info(f"Appointment stats: today={appointments_today}, month={appointments_this_month}")
        
        # Статистика по доходам
        monthly_revenue = Booking.objects.filter(
            master=employee,
            date__gte=month_ago.date()
        ).aggregate(total=Sum('price'))['total'] or 0
        
        avg_ticket = Booking.objects.filter(
            master=employee,
            date__gte=month_ago.date()
        ).aggregate(avg=Avg('price'))['avg'] or 0
        
        logger.info(f"Revenue stats: monthly={monthly_revenue}, avg_ticket={avg_ticket}")
        
        # Популярные услуги
        popular_services = Booking.objects.filter(
            master=employee,
            date__gte=month_ago.date()
        ).values('service__name').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        logger.info(f"Popular services: {list(popular_services)}")
        
        # Топ клиенты
        top_clients = Client.objects.filter(
            bookings__master=employee
        ).annotate(
            booking_count=Count('bookings'),
            top_total_spent=Sum('bookings__price')
        ).order_by('-top_total_spent')[:3]
        
        logger.info(f"Top clients count: {top_clients.count()}")
        
        # Анализируем сообщение пользователя
        lower_message = user_message.lower()
        logger.info(f"Processing message: '{user_message}' -> '{lower_message}'")
        
        # Ответы на основе контекста
        if any(word in lower_message for word in ['клиент', 'клиенты', 'база']):
            if 'новый' in lower_message or 'новые' in lower_message:
                response = f"За этот месяц у вас появилось {new_clients_this_month} новых клиентов. Отличная работа по привлечению!"
            elif 'всего' in lower_message or 'общее' in lower_message:
                response = f"В вашей базе {total_clients} клиентов. За месяц прибавилось {new_clients_this_month} новых."
            else:
                response = f"У вас {total_clients} клиентов в базе. За месяц рост составил {new_clients_this_month} новых клиентов."
        elif any(word in lower_message for word in ['доход', 'выручка', 'заработок', 'деньги']):
            if 'месяц' in lower_message or 'месячный' in lower_message:
                response = f"Ваш доход за месяц составляет ₽{monthly_revenue:,}. Средний чек: ₽{avg_ticket:,.0f}."
            elif 'сегодня' in lower_message:
                response = f"Сегодня у вас {appointments_today} записей. Примерный доход за день: ₽{appointments_today * avg_ticket:,.0f}."
            else:
                response = f"Ваш месячный доход: ₽{monthly_revenue:,}. Средний чек: ₽{avg_ticket:,.0f}."
        elif any(word in lower_message for word in ['запись', 'записи', 'расписание', 'график']):
            if 'сегодня' in lower_message:
                response = f"Сегодня у вас {appointments_today} записей. {'Отличная загрузка!' if appointments_today > 5 else 'Можно добавить еще клиентов.'}"
            elif 'месяц' in lower_message or 'месячный' in lower_message:
                response = f"За месяц у вас {appointments_this_month} записей. Средняя загрузка: {appointments_this_month // 30} записей в день."
            else:
                response = f"Сегодня: {appointments_today} записей. За месяц: {appointments_this_month} записей."
        elif any(word in lower_message for word in ['услуга', 'услуги', 'популярн']):
            if popular_services:
                services_list = ", ".join([s['service__name'] for s in popular_services])
                response = f"Ваши популярные услуги: {services_list}. Фокусируйтесь на продвижении этих услуг."
            else:
                response = "Пока недостаточно данных для анализа популярных услуг. Продолжайте работать с клиентами!"
        elif any(word in lower_message for word in ['топ', 'лучш', 'активн']):
            if top_clients:
                top_client = top_clients[0]
                response = f"Ваш топ-клиент: {top_client.name} - {top_client.booking_count} визитов, потратил ₽{top_client.top_total_spent or 0:,}."
            else:
                response = "Пока нет данных о топ-клиентах. Продолжайте работать с клиентами!"
        elif any(word in lower_message for word in ['помощь', 'что умеешь', 'функции', 'возможности']):
            response = "Я могу рассказать о ваших клиентах, записях, доходах, популярных услугах и топ-клиентах. Просто спросите меня о любых данных!"
        elif any(word in lower_message for word in ['привет', 'здравствуй', 'добрый день', 'доброе утро']):
            response = f"Привет! У вас {appointments_today} записей на сегодня. Чем могу помочь?"
        elif any(word in lower_message for word in ['спасибо', 'благодарю', 'спс']):
            response = "Пожалуйста! Всегда рад помочь. Если есть еще вопросы - обращайтесь!"
        elif any(word in lower_message for word in ['статистика', 'аналитика', 'данные']):
            response = f"Ваша статистика: {total_clients} клиентов, {appointments_this_month} записей за месяц, доход ₽{monthly_revenue:,}."
        else:
            # Общие ответы с контекстом
            general_responses = [
                f"Интересный вопрос! У вас {total_clients} клиентов и {appointments_today} записей на сегодня.",
                f"Хороший вопрос! Ваш доход за месяц составляет ₽{monthly_revenue:,}.",
                f"Отличный вопрос! У вас {new_clients_this_month} новых клиентов за месяц.",
                f"Интересно! Ваши данные показывают стабильную работу с клиентами.",
                f"Спасибо за вопрос! Ваша статистика: {appointments_this_month} записей за месяц."
            ]
            response = general_responses[hash(user_message) % len(general_responses)]
        
        logger.info(f"Generated response: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_ai_chat_response: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Извините, произошла ошибка при обработке вашего запроса: {str(e)}"

def employee_dashboard(request):
    """Function-based view для employee dashboard"""
    if not request.user.is_authenticated:
        return redirect('/login/')
    if not hasattr(request.user, 'employee') or not request.user.employee.is_master:
        return redirect('/dashboard/')
    lang = get_user_language(request)
    is_mob = is_mobile(request)
    template = f"employee/{lang}/employee_dashboard_mobile.html" if is_mob else f"employee/{lang}/employee_dashboard.html"
    return render(request, template, {"current_language": lang})

def employee_overview(request):
    """Function-based view для employee overview API"""
    user = request.user
    if not hasattr(user, 'employee') or not user.employee.is_master:
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    
    employee = user.employee
    today = timezone.now().date()
    current_month = timezone.now().month
    current_year = timezone.now().year
    total_clients = Client.objects.filter(bookings__master=employee).distinct().count()
    appointments_today = Booking.objects.filter(master=employee, date=today).count()
    monthly_revenue = Booking.objects.filter(master=employee, date__month=current_month, date__year=current_year).aggregate(total=Sum('price'))['total'] or 0
    avg_ticket = Booking.objects.filter(master=employee).aggregate(avg=Avg('price'))['avg'] or 0
    
    # Рост по сравнению с прошлым месяцем
    last_month = current_month - 1 if current_month > 1 else 12
    last_month_year = current_year if current_month > 1 else current_year - 1
    last_month_revenue = Booking.objects.filter(master=employee, date__month=last_month, date__year=last_month_year).aggregate(total=Sum('price'))['total'] or 0
    last_month_clients = Client.objects.filter(bookings__master=employee, bookings__date__month=last_month, bookings__date__year=last_month_year).distinct().count()
    current_month_clients = Client.objects.filter(bookings__master=employee, bookings__date__month=current_month, bookings__date__year=current_year).distinct().count()
    last_month_appointments = Booking.objects.filter(master=employee, date__month=last_month, date__year=last_month_year).count()
    current_month_appointments = Booking.objects.filter(master=employee, date__month=current_month, date__year=current_year).count()
    last_month_avg_ticket = Booking.objects.filter(master=employee, date__month=last_month, date__year=last_month_year).aggregate(avg=Avg('price'))['avg'] or 0
    
    revenue_growth = ((monthly_revenue - last_month_revenue) / last_month_revenue) * 100 if last_month_revenue > 0 else 0
    clients_growth = ((current_month_clients - last_month_clients) / last_month_clients) * 100 if last_month_clients > 0 else (current_month_clients * 100 if current_month_clients > 0 else 0)
    appointments_growth = ((current_month_appointments - last_month_appointments) / last_month_appointments) * 100 if last_month_appointments > 0 else (current_month_appointments * 100 if current_month_appointments > 0 else 0)
    avg_ticket_change = ((avg_ticket - last_month_avg_ticket) / last_month_avg_ticket) * 100 if last_month_avg_ticket > 0 else 0
    
    total_employees = Employee.objects.filter(is_master=True).count()
    total_services = Service.objects.count()
    
    data = {
        'total_clients': total_clients,
        'appointments_today': appointments_today,
        'monthly_revenue': float(monthly_revenue),
        'avg_ticket': float(avg_ticket),
        'clients_growth': round(clients_growth, 1),
        'revenue_growth': round(revenue_growth, 1),
        'appointments_growth': round(appointments_growth, 1),
        'avg_ticket_change': round(avg_ticket_change, 1),
        'user_name': employee.name,
        'total_employees': total_employees,
        'total_services': total_services,
    }
    
    return JsonResponse(data)

def employee_revenue_chart(request):
    """Function-based view для employee revenue chart API"""
    user = request.user
    if not hasattr(user, 'employee') or not user.employee.is_master:
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    
    employee = user.employee
    period = request.GET.get('period', 'week')
    now = timezone.now().date()
    
    if period == 'year':
        labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        revenue, bookings, clients = [], [], []
        for month in range(1, 13):
            revenue_val = Booking.objects.filter(master=employee, date__year=now.year, date__month=month).aggregate(total=Sum('price'))['total'] or 0
            bookings_val = Booking.objects.filter(master=employee, date__year=now.year, date__month=month).count()
            clients_val = Client.objects.filter(bookings__master=employee, bookings__date__year=now.year, bookings__date__month=month).distinct().count()
            revenue.append(float(revenue_val))
            bookings.append(bookings_val)
            clients.append(clients_val)
    elif period == 'month':
        import calendar
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        labels = [str(day) for day in range(1, days_in_month + 1)]
        revenue, bookings, clients = [], [], []
        for day in range(1, days_in_month + 1):
            date = now.replace(day=day)
            revenue_val = Booking.objects.filter(master=employee, date=date).aggregate(total=Sum('price'))['total'] or 0
            bookings_val = Booking.objects.filter(master=employee, date=date).count()
            clients_val = Client.objects.filter(bookings__master=employee, bookings__date=date).distinct().count()
            revenue.append(float(revenue_val))
            bookings.append(bookings_val)
            clients.append(clients_val)
    else:
        end_date = now
        start_date = end_date - timedelta(days=6)
        dates = [end_date - timedelta(days=i) for i in range(6, -1, -1)]
        day_names = {0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'}
        labels = [day_names[date.weekday()] for date in dates]
        revenue, bookings, clients = [], [], []
        for date in dates:
            revenue_val = Booking.objects.filter(master=employee, date=date).aggregate(total=Sum('price'))['total'] or 0
            bookings_val = Booking.objects.filter(master=employee, date=date).count()
            clients_val = Client.objects.filter(bookings__master=employee, bookings__date=date).distinct().count()
            revenue.append(float(revenue_val))
            bookings.append(bookings_val)
            clients.append(clients_val)
    
    chart_data = {
        'labels': labels,
        'revenue': revenue,
        'bookings': bookings,
        'clients': clients
    }
    
    return JsonResponse(chart_data)

def employee_ai_advice(request):
    """Function-based view для employee AI advice API"""
    user = request.user
    if not hasattr(user, 'employee') or not user.employee.is_master:
        return JsonResponse([], status=403)
    
    employee = user.employee
    force_update = request.GET.get('force_update') == 'true'
    result = get_employee_ai_advices_from_db_or_trigger_bg(employee, force_update=force_update)
    advices = result['advices']
    
    return JsonResponse({'pending': False, 'advices': advices})

def employee_top_clients(request):
    """Function-based view для employee top clients API"""
    user = request.user
    if not hasattr(user, 'employee') or not user.employee.is_master:
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    
    employee = user.employee
    top_clients = Client.objects.filter(bookings__master=employee).annotate(
        booking_count=Count('bookings'),
        top_total_spent=Sum('bookings__price')
    ).order_by('-top_total_spent')[:5]
    
    clients_data = []
    for client in top_clients:
        clients_data.append({
            'id': client.id,
            'name': client.name,
            'phone': client.phone,
            'booking_count': client.booking_count,
            'total_spent': float(client.top_total_spent or 0)
        })
    
    return JsonResponse(clients_data, safe=False)

def employee_recent_activity(request):
    """Function-based view для employee recent activity API"""
    user = request.user
    if not hasattr(user, 'employee') or not user.employee.is_master:
        return JsonResponse({'activities': [], 'error': 'Нет доступа'}, status=403)
    
    employee = user.employee
    activities = []
    
    def get_time_ago(timestamp):
        now = timezone.now()
        diff = now - timestamp
        if diff.days > 0:
            return f"{diff.days} дней назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} часов назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} минут назад"
        else:
            return "Только что"
    
    recent_bookings = Booking.objects.filter(master=employee).order_by('-created_at')[:5]
    for booking in recent_bookings:
        time_ago = get_time_ago(booking.created_at)
        activities.append({
            'id': f'booking_{booking.id}',
            'action': f'Новая запись: {booking.service.name}',
            'time_ago': time_ago,
            'extra': {
                'client': booking.client.name,
                'service': booking.service.name,
                'amount': booking.price,
                'date': booking.date.strftime('%d.%m.%Y'),
                'time': booking.start_time.strftime('%H:%M')
            }
        })
    
    recent_clients = Client.objects.filter(bookings__master=employee).order_by('-created_at')[:3]
    for client in recent_clients:
        time_ago = get_time_ago(client.created_at)
        activities.append({
            'id': f'client_{client.id}',
            'action': 'Новый клиент зарегистрирован',
            'time_ago': time_ago,
            'extra': {
                'client_name': client.name,
                'phone': client.phone,
                'status': client.get_status_display()
            }
        })
    
    activities.sort(key=lambda x: x.get('time_ago', ''), reverse=True)
    activities = activities[:10]
    
    return JsonResponse({'activities': activities})

class EmployeeClientPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class EmployeeClientListAPIView(generics.ListAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EmployeeClientPagination

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'employee') and user.employee.is_master:
            return Client.objects.filter(bookings__master=user.employee).distinct().order_by('-created_at')
        return Client.objects.none()

class EmployeeOnlyMixin:
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or not hasattr(user, 'employee') or not user.employee.is_master:
            if user.is_authenticated and (user.is_superuser or user.is_staff):
                return HttpResponseRedirect('/dashboard/')
            return HttpResponseRedirect('/')
        return super().dispatch(request, *args, **kwargs)

class EmployeeClientsPageView(EmployeeOnlyMixin, TemplateView):
    def get_template_names(self):
        lang = get_user_language(self.request)
        is_mob = is_mobile(self.request)
        if is_mob:
            return [f"employee/{lang}/employee_clients.html"]
        return [f"employee/{lang}/employee_clients_desktop.html"]
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_language"] = get_user_language(self.request)
        return context

class EmployeeBookingPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500

class EmployeeBookingListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = EmployeeBookingPagination

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'employee') and user.employee.is_master:
            return Booking.objects.filter(master=user.employee).select_related('client', 'service').order_by('-date', '-start_time')
        return Booking.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'employee') and user.employee.is_master:
            serializer.save(master=user.employee)
        else:
            raise PermissionDenied('Вы не мастер')

class EmployeeBookingRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'employee') and user.employee.is_master:
            return Booking.objects.filter(master=user.employee)
        return Booking.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        if hasattr(user, 'employee') and user.employee.is_master:
            serializer.save(master=user.employee)
        else:
            raise PermissionDenied('Вы не мастер')

    def perform_destroy(self, instance):
        user = self.request.user
        if hasattr(user, 'employee') and user.employee.is_master and instance.master == user.employee:
            instance.delete()
        else:
            raise PermissionDenied('Вы не мастер или не ваша запись')

class EmployeeSchedulesPageView(EmployeeOnlyMixin, TemplateView):
    def get_template_names(self):
        lang = get_user_language(self.request)
        is_mob = is_mobile(self.request)
        if is_mob:
            return [f"employee/{lang}/employee_schedules.html"]
        return [f"employee/{lang}/employee_schedules_desktop.html"]
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_language"] = get_user_language(self.request)
        return context

class EmployeeNotificationsPageView(EmployeeOnlyMixin, TemplateView):
    def get_template_names(self):
        lang = get_user_language(self.request)
        is_mob = is_mobile(self.request)
        if is_mob:
            return [f"employee/{lang}/employee_notifications_mobile.html"]
        return [f"employee/{lang}/employee_notifications.html"]
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_language"] = get_user_language(self.request)
        return context

class EmployeeSettingsPageView(EmployeeOnlyMixin, TemplateView):
    def get_template_names(self):
        lang = get_user_language(self.request)
        is_mob = is_mobile(self.request)
        if is_mob:
            return [f"employee/{lang}/employee_settings_mobile.html"]
        return [f"employee/{lang}/employee_settings.html"]
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_language"] = get_user_language(self.request)
        return context

class EmployeeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            'id', 'user', 'business', 'name', 'position', 'phone', 'email', 'status', 'experience', 'birthDate',
            'education', 'skills', 'address', 'salary', 'schedule', 'clientsCount', 'rating', 'photo', 'is_master',
            'workSchedule', 'languages', 'achievements', 'notes', 'equipment', 'certifications',
            'emergencyContact', 'emergencyContactName', 'emergencyContactRelation',
            'passportNumber', 'passportIssued', 'passportExpiry',
            'taxId', 'bankAccount', 'bankName',
            'startDate', 'contractNumber', 'contractExpiry',
            'vacationDaysTotal', 'vacationDaysUsed',
            'sickDaysTotal', 'sickDaysUsed',
            'insuranceNumber', 'insuranceExpiry',
            'performanceReviews', 'trainingHistory', 'salaryHistory', 'documents'
        ]

class EmployeeProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, 'employee') or not user.employee.is_master:
            return Response({'error': 'Нет доступа'}, status=403)
        serializer = EmployeeProfileSerializer(user.employee)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        if not hasattr(user, 'employee') or not user.employee.is_master:
            return Response({'error': 'Нет доступа'}, status=403)
        serializer = EmployeeProfileSerializer(user.employee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class IsEmployeeMaster(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and hasattr(user, 'employee') and user.employee.is_master

EmployeeDashboardOverviewView.permission_classes = [IsEmployeeMaster]
EmployeeRevenueChartView.permission_classes = [IsEmployeeMaster]
EmployeeAIInsightsView.permission_classes = [IsEmployeeMaster]
EmployeeTopClientsView.permission_classes = [IsEmployeeMaster]
EmployeeRecentActivityView.permission_classes = [IsEmployeeMaster]
EmployeeProfileAPIView.permission_classes = [IsEmployeeMaster]
EmployeeClientListAPIView.permission_classes = [IsEmployeeMaster]
EmployeeBookingListCreateAPIView.permission_classes = [IsEmployeeMaster]
EmployeeBookingRetrieveUpdateDestroyAPIView.permission_classes = [IsEmployeeMaster]
