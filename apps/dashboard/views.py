from django.shortcuts import redirect, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum, Count, Avg, Q
from decimal import Decimal
from django.views.generic import TemplateView
import traceback
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator

from .models import BusinessStats, FinanceRecord, ActivityLog, AIAdvice
from .serializers import (
    BusinessStatsSerializer, 
    FinanceRecordSerializer, 
    ActivityLogSerializer,
    DashboardOverviewSerializer,
    RevenueChartSerializer,
    RecentActivitySerializer,
    AIInsightSerializer
)
from apps.businesses.models import Business
from apps.accounts.models import User
from apps.clients.models import Client
from apps.schedules.models import Booking
from apps.services.models import Service
from apps.employees.models import Employee
from .utils import generate_ai_advices, create_unavailable_message, get_ai_advices_from_db_or_trigger_bg
from apps.clients.serializers import ClientSerializer
from apps.services.serializers import ServiceSerializer

def admin_or_owner_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        is_admin = user.is_superuser or (hasattr(user, 'role') and getattr(user, 'role', None) == User.Role.ADMIN)
        if not user.is_authenticated or not is_admin:
            if hasattr(user, 'employee') and getattr(user.employee, 'is_master', False):
                return HttpResponseRedirect('/employee/')
            return HttpResponseRedirect('/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

class AdminOrOwnerOnlyMixin:
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        is_admin = user.is_superuser or (hasattr(user, 'role') and getattr(user, 'role', None) == User.Role.ADMIN)
        if not user.is_authenticated or not is_admin:
            if hasattr(user, 'employee') and getattr(user.employee, 'is_master', False):
                return HttpResponseRedirect('/employee/')
            return HttpResponseRedirect('/')
        return super().dispatch(request, *args, **kwargs)

class DashboardOverviewView(APIView):
    """Общая статистика для dashboard по бизнесу пользователя"""
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'business') or not request.user.business:
            return Response({'error': 'Нет доступа или бизнес не найден'}, status=403)
        business = request.user.business
        try:
            today = timezone.now().date()
            current_month = timezone.now().month
            current_year = timezone.now().year

            # Отладочная информация
            print(f"DEBUG: Пользователь: {request.user}")
            print(f"DEBUG: Имя пользователя: {request.user.full_name}")
            print(f"DEBUG: Аутентифицирован: {request.user.is_authenticated}")
            print(f"DEBUG: Бизнес: {business.name}")

            total_clients = Client.objects.filter(business=business).count()
            appointments_today = Booking.objects.filter(service__business=business, date=today).count()
            monthly_revenue = Booking.objects.filter(service__business=business, date__month=current_month, date__year=current_year).aggregate(total=Sum('price'))['total'] or 0
            avg_ticket = Booking.objects.filter(service__business=business).aggregate(avg=Avg('price'))['avg'] or 0
            total_employees = Employee.objects.filter(business=business, status='active').count()
            total_services = Service.objects.filter(business=business, is_active=True).count()
            active_businesses = 1

            last_month = current_month - 1 if current_month > 1 else 12
            last_month_year = current_year if current_month > 1 else current_year - 1
            
            last_month_revenue = Booking.objects.filter(service__business=business, date__month=last_month, date__year=last_month_year).aggregate(total=Sum('price'))['total'] or 0
            last_month_clients = Client.objects.filter(business=business, created_at__month=last_month, created_at__year=last_month_year).count()
            current_month_clients = Client.objects.filter(business=business, created_at__month=current_month, created_at__year=current_year).count()
            last_month_appointments = Booking.objects.filter(service__business=business, date__month=last_month, date__year=last_month_year).count()
            current_month_appointments = Booking.objects.filter(service__business=business, date__month=current_month, date__year=current_year).count()
            last_month_avg_ticket = Booking.objects.filter(service__business=business, date__month=last_month, date__year=last_month_year).aggregate(avg=Avg('price'))['avg'] or 0

            revenue_growth = ((monthly_revenue - last_month_revenue) / last_month_revenue) * 100 if last_month_revenue > 0 else 0
            clients_growth = ((current_month_clients - last_month_clients) / last_month_clients) * 100 if last_month_clients > 0 else (current_month_clients * 100 if current_month_clients > 0 else 0)
            appointments_growth = ((current_month_appointments - last_month_appointments) / last_month_appointments) * 100 if last_month_appointments > 0 else (current_month_appointments * 100 if current_month_appointments > 0 else 0)
            avg_ticket_change = ((avg_ticket - last_month_avg_ticket) / last_month_avg_ticket) * 100 if last_month_avg_ticket > 0 else 0

            user_name = request.user.full_name if request.user.is_authenticated else 'Пользователь'
            print(f"DEBUG: Возвращаемое имя пользователя: {user_name}")

            data = {
                'total_clients': total_clients,
                'appointments_today': appointments_today,
                'monthly_revenue': float(monthly_revenue),
                'avg_ticket': float(avg_ticket),
                'clients_growth': round(clients_growth, 1),
                'revenue_growth': round(revenue_growth, 1),
                'appointments_growth': round(appointments_growth, 1),
                'avg_ticket_change': round(avg_ticket_change, 1),
                'total_employees': total_employees,
                'total_services': total_services,
                'active_businesses': active_businesses,
                'user_name': user_name,
            }
            print(f"DEBUG: Полные данные API: {data}")
            serializer = DashboardOverviewSerializer(data)
            return Response(serializer.data)
        except Exception as e:
            print(f"ERROR: Ошибка в DashboardOverviewView: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RevenueChartView(APIView):
    """Данные для графика доходов, записей и клиентов по бизнесу пользователя с поддержкой фильтра по периоду"""
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'business') or not request.user.business:
            return Response({'error': 'Нет доступа или бизнес не найден'}, status=403)
        business = request.user.business
        try:
            period = request.GET.get('period', 'week')
            now = timezone.now().date()
            if period == 'year':
                # Год: по месяцам
                labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
                revenue = []
                bookings = []
                clients = []
                for month in range(1, 13):
                    revenue_val = Booking.objects.filter(
                        service__business=business,
                        date__year=now.year,
                        date__month=month
                    ).aggregate(total=Sum('price'))['total'] or 0
                    bookings_val = Booking.objects.filter(
                        service__business=business,
                        date__year=now.year,
                        date__month=month
                    ).count()
                    clients_val = Client.objects.filter(
                        business=business,
                        created_at__year=now.year,
                        created_at__month=month
                    ).count()
                    revenue.append(float(revenue_val))
                    bookings.append(bookings_val)
                    clients.append(clients_val)
            elif period == 'month':
                # Месяц: по дням текущего месяца
                import calendar
                days_in_month = calendar.monthrange(now.year, now.month)[1]
                labels = [str(day) for day in range(1, days_in_month + 1)]
                revenue = []
                bookings = []
                clients = []
                for day in range(1, days_in_month + 1):
                    date = now.replace(day=day)
                    revenue_val = Booking.objects.filter(
                        service__business=business,
                        date=date
                    ).aggregate(total=Sum('price'))['total'] or 0
                    bookings_val = Booking.objects.filter(
                        service__business=business,
                        date=date
                    ).count()
                    clients_val = Client.objects.filter(
                        business=business,
                        created_at__date=date
                    ).count()
                    revenue.append(float(revenue_val))
                    bookings.append(bookings_val)
                    clients.append(clients_val)
            else:
                # Неделя (по умолчанию): последние 7 дней
                end_date = now
                start_date = end_date - timedelta(days=6)
                dates = [end_date - timedelta(days=i) for i in range(6, -1, -1)]
                labels = [self._get_russian_day_name(date) for date in dates]
                revenue = []
                bookings = []
                clients = []
            for date in dates:
                    revenue_val = Booking.objects.filter(
                        service__business=business,
                        date=date
                    ).aggregate(total=Sum('price'))['total'] or 0
                    bookings_val = Booking.objects.filter(
                        service__business=business,
                    date=date
                    ).count()
                    clients_val = Client.objects.filter(
                        business=business,
                        created_at__date=date
                    ).count()
                    revenue.append(float(revenue_val))
                    bookings.append(bookings_val)
                    clients.append(clients_val)
            chart_data = {
                'labels': labels,
                'revenue': revenue,
                'bookings': bookings,
                'clients': clients
            }
            serializer = RevenueChartSerializer(chart_data)
            return Response(serializer.data)
        except Exception as e:
            print(f"ERROR: Ошибка в RevenueChartView: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_russian_day_name(self, date):
        """Возвращает название дня недели на русском языке"""
        day_names = {
            0: 'Пн',
            1: 'Вт', 
            2: 'Ср',
            3: 'Чт',
            4: 'Пт',
            5: 'Сб',
            6: 'Вс'
        }
        return day_names[date.weekday()]

class RecentActivityView(APIView):
    """Последние действия по бизнесу пользователя"""
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'business') or not request.user.business:
            return Response({'activities': [], 'error': 'Нет доступа или бизнес не найден'}, status=403)
        business = request.user.business
        # Определяем язык (аналогично DashboardTemplateView)
        lang_param = request.GET.get('lang')
        lang = None
        user = getattr(request, 'user', None)
        if lang_param in ['ru', 'ky']:
            lang = lang_param
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
        try:
            activities = []
            recent_bookings = Booking.objects.filter(service__business=business).order_by('-created_at')[:5]
            for booking in recent_bookings:
                time_ago = self._get_time_ago(booking.created_at)
                if lang == 'ky':
                    action = f'Жаңы жазылуу: {booking.service.name}'
                else:
                    action = f'Новая запись: {booking.service.name}'
                activities.append({
                    'id': f'booking_{booking.id}',
                    'action': action,
                    'time_ago': time_ago,
                    'extra': {
                        'client': booking.client.name,
                        'service': booking.service.name,
                        'amount': booking.price,
                        'date': booking.date.strftime('%d.%m.%Y'),
                        'time': booking.start_time.strftime('%H:%M')
                    }
                })
            recent_clients = Client.objects.filter(business=business).order_by('-created_at')[:3]
            for client in recent_clients:
                time_ago = self._get_time_ago(client.created_at)
                action = 'Жаңы клиент катталды' if lang == 'ky' else 'Новый клиент зарегистрирован'
                activities.append({
                    'id': f'client_{client.id}',
                    'action': action,
                    'time_ago': time_ago,
                    'extra': {
                        'client_name': client.name,
                        'phone': client.phone,
                        'status': client.get_status_display()
                    }
                })
            recent_employees = Employee.objects.filter(business=business).order_by('-id')[:2]
            for employee in recent_employees:
                action = 'Жаңы кызматкер кошулду' if lang == 'ky' else 'Новый сотрудник добавлен'
                activities.append({
                    'id': f'employee_{employee.id}',
                    'action': action,
                    'time_ago': 'Жакында' if lang == 'ky' else 'Недавно',
                    'extra': {
                        'employee_name': employee.name,
                        'position': employee.position.name if employee.position else ('Көрсөтүлгөн эмес' if lang == 'ky' else 'Не указана')
                    }
                })
            activities.sort(key=lambda x: x.get('time_ago', ''), reverse=True)
            activities = activities[:10]
            return Response({'activities': activities})
        except Exception as e:
            return Response({'activities': [], 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_time_ago(self, timestamp):
        """Возвращает относительное время"""
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

class AIInsightsView(APIView):
    """ИИ-советы для бизнеса с автоматическим обновлением через g4f"""
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'business') or not request.user.business:
            return Response([], status=403)
        business = request.user.business
        # Определяем язык (аналогично DashboardTemplateView)
        lang_param = request.GET.get('lang')
        lang = None
        user = getattr(request, 'user', None)
        if lang_param in ['ru', 'ky']:
            lang = lang_param
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
        try:
            force_update = request.query_params.get('force_update') == 'true'
            if force_update:
                advices = generate_ai_advices(business, lang=lang)
                if advices:
                    from .models import AIAdvice
                    obj, _ = AIAdvice.objects.get_or_create(business=business)
                    obj.data = advices
                    obj.save(update_fields=["data", "updated_at"])
                else:
                    from .utils import create_unavailable_message
                    advices = create_unavailable_message(lang=lang)
                from .serializers import AIInsightSerializer
                serializer = AIInsightSerializer(advices, many=True)
                return Response({'pending': False, 'advices': serializer.data})
            else:
                result = get_ai_advices_from_db_or_trigger_bg(business, lang=lang)
                from .serializers import AIInsightSerializer
                serializer = AIInsightSerializer(result['advices'], many=True)
                return Response({'pending': result['pending'], 'advices': serializer.data})
        except Exception as e:
            print(f"ERROR: AIInsightsView: {e}")
            from .utils import create_unavailable_message
            advices = create_unavailable_message(lang=lang)
            from .serializers import AIInsightSerializer
            serializer = AIInsightSerializer(advices, many=True)
            return Response({'pending': False, 'advices': serializer.data}, status=500)

class BusinessStatsView(APIView):
    """Детальная статистика бизнеса"""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            business = Business.objects.filter(owner=request.user).first()
            if not business:
                return Response(
                    {"error": "Бизнес не найден"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            stats = BusinessStats.objects.filter(business=business).first()
            if not stats:
                stats = BusinessStats.objects.create(business=business)

            serializer = BusinessStatsSerializer(stats)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FinanceRecordsView(APIView):
    """Финансовые записи"""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            business = Business.objects.filter(owner=request.user).first()
            if not business:
                return Response(
                    {"error": "Бизнес не найден"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Получаем финансовые записи за последние 30 дней
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            records = FinanceRecord.objects.filter(
                business=business,
                date__range=[start_date, end_date]
            ).order_by('-date')

            serializer = FinanceRecordSerializer(records, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Создание новой финансовой записи"""
        try:
            business = Business.objects.filter(owner=request.user).first()
            if not business:
                return Response(
                    {"error": "Бизнес не найден"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            data = request.data.copy()
            data['business'] = business.id

            serializer = FinanceRecordSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DashboardTemplateView(TemplateView):
    def get(self, request, *args, **kwargs):
        # 1. Язык из GET-параметра (ручной переключатель)
        lang_param = request.GET.get('lang')
        lang = None
        user = getattr(request, 'user', None)
        if lang_param in ['ru', 'ky']:
            lang = lang_param
            # Если пользователь авторизован — сохранить в профиль
            if user and user.is_authenticated:
                if hasattr(user, 'preferred_language') and getattr(user, 'preferred_language', None) != lang_param:
                    user.preferred_language = lang_param
                    user.save(update_fields=["preferred_language"])
            else:
                request.session['preferred_language'] = lang_param
        # 2. Язык из профиля пользователя
        if not lang and user and user.is_authenticated:
            lang = getattr(user, 'preferred_language', None)
        # 3. Язык из сессии (для гостей)
        if not lang:
            lang = request.session.get('preferred_language')
        # 4. Язык из заголовка браузера
        if not lang:
            accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '').lower()
            if accept_lang.startswith('ky'):
                lang = 'ky'
            elif accept_lang.startswith('ru'):
                lang = 'ru'
        # 5. По умолчанию — русский
        if lang not in ['ru', 'ky']:
            lang = 'ru'
        # Определяем мобильность
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_mobile = any(mob in user_agent for mob in ['iphone', 'android', 'blackberry', 'mobile', 'opera mini', 'windows phone'])
        # Выбираем шаблон
        template = f"{lang}/dashboard_mobile.html" if is_mobile else f"{lang}/dashboard.html"

        # Проверка тарифа
        is_tarifed = True
        is_trial = False
        trial_expired = False
        show_dashboard_welcome = False
        overview = None
        if user and user.is_authenticated:
            is_tarifed = getattr(user, 'is_tarifed', True)
            is_trial = getattr(user, 'is_trial', False)
            trial_expired = (not is_trial) and (not is_tarifed)
            if not getattr(user, 'is_dashboard_welcome_showed', False):
                show_dashboard_welcome = True
                overview = {
                    'user_name': 'Демо Бизнес',
                    'total_clients': 42,
                    'appointments_today': 5,
                    'monthly_revenue': 123456,
                    'avg_ticket': 3000,
                    'clients_growth': 12,
                    'revenue_growth': 8,
                    'appointments_growth': 5,
                    'avg_ticket_change': 2,
                    'total_employees': 7,
                    'total_services': 10,
                    'active_businesses': 1
                }
        context = {
            "current_language": lang,
            "is_tarifed": is_tarifed,
            "is_trial": is_trial,
            "trial_expired": trial_expired,
            "show_dashboard_welcome": show_dashboard_welcome,
            "show_demo_offer": user and user.is_authenticated and not getattr(user, 'is_dashboard_welcome_showed', False),
        }
        if overview:
            context["overview"] = overview
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            user.is_dashboard_welcome_showed = True
            user.save(update_fields=["is_dashboard_welcome_showed"])
        return redirect(request.path)

class PopularServicesView(APIView):
    """Популярные услуги по бизнесу пользователя"""
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'business') or not request.user.business:
            return Response({'error': 'Нет доступа или бизнес не найден'}, status=403)
        business = request.user.business
        try:
            popular_services = Service.objects.filter(business=business, is_active=True).annotate(booking_count=Count('booking')).order_by('-booking_count')[:5]
            services_data = []
            for service in popular_services:
                services_data.append({
                    'id': service.id,
                    'name': service.name,
                    'price': service.price,
                    'booking_count': service.booking_count,
                    'category': service.category.name if service.category else 'Без категории'
                })
            return Response(services_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TopClientsView(APIView):
    """Топ клиентов по бизнесу пользователя"""
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'business') or not request.user.business:
            return Response({'error': 'Нет доступа или бизнес не найден'}, status=403)
        business = request.user.business
        try:
            top_clients = Client.objects.filter(business=business).annotate(booking_count=Count('bookings')).order_by('-booking_count')[:5]
            clients_data = []
            for client in top_clients:
                clients_data.append({
                    'id': client.id,
                    'name': client.name,
                    'phone': client.phone,
                    'booking_count': client.booking_count,
                    'total_spent': float(client.total_spent),
                    'status': client.get_status_display()
                })
            return Response(clients_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AllServicesAPIView(APIView):
    """Список всех услуг текущего бизнеса пользователя"""
    permission_classes = [AllowAny]
    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'business') or not request.user.business:
            return Response([], status=403)
        business = request.user.business
        services = Service.objects.filter(business=business, is_active=True)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

class AllClientsAPIView(APIView):
    """Список всех клиентов текущего бизнеса пользователя"""
    permission_classes = [AllowAny]
    def get(self, request):
        if not request.user.is_authenticated or not hasattr(request.user, 'business') or not request.user.business:
            return Response([], status=403)
        business = request.user.business
        clients = Client.objects.filter(business=business)
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)

class DashboardDemoTemplateView(TemplateView):
    def get(self, request, *args, **kwargs):
        # Определяем язык (аналогично DashboardTemplateView)
        lang_param = request.GET.get('lang')
        lang = None
        user = getattr(request, 'user', None)
        if lang_param in ['ru', 'ky']:
            lang = lang_param
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
        
        # Выбираем шаблон
        template = f"{lang}/demo/dashboard.html"
        
        # Контекст для демо-версии
        context = {
            "current_language": lang,
            "is_tarifed": True,  # В демо всегда показываем как тарифицированный
            "days_left": 0,  # Пробный период завершен
        }
        
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            user.is_dashboard_welcome_showed = True
            user.save(update_fields=["is_dashboard_welcome_showed"])
        return redirect("/dashboard/")

# Обернуть все CBV
for cls in [DashboardOverviewView, RevenueChartView, RecentActivityView, AIInsightsView, BusinessStatsView, FinanceRecordsView, DashboardTemplateView, PopularServicesView, TopClientsView, AllServicesAPIView, AllClientsAPIView]:
    cls.dispatch = method_decorator(admin_or_owner_required)(cls.dispatch)
