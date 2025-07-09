from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg, Sum
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model
from .models import Employee, Position
from .serializers import EmployeeSerializer, EmployeeCreateSerializer, EmployeeUpdateSerializer, PositionSerializer, BusinessTypeSerializer, BusinessSubtypeSerializer, EmployeeShortSerializer
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from apps.businesses.models import BusinessType, BusinessSubtype
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
import requests

User = get_user_model()

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

class EmployeeViewSet(AdminOrOwnerOnlyMixin, viewsets.ModelViewSet):
    """
    API endpoint для управления сотрудниками
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EmployeeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmployeeUpdateSerializer
        return EmployeeSerializer
    
    def get_queryset(self):
        """
        Фильтруем сотрудников по бизнесу текущего пользователя
        """
        queryset = super().get_queryset()
        is_master = self.request.query_params.get('is_master')
        if is_master is not None:
            queryset = queryset.filter(is_master=is_master in ['1', 'true', 'True'])
        
        user = self.request.user
        
        # Если пользователь админ, показываем всех сотрудников его бизнеса
        if user.role == User.Role.ADMIN and user.business:
            queryset = queryset.filter(business=user.business)
        # Если пользователь сотрудник, показываем только себя
        elif user.role == User.Role.EMPLOYEE:
            try:
                queryset = queryset.filter(user=user)
            except Employee.DoesNotExist:
                queryset = Employee.objects.none()
        else:
            # Для обычных пользователей - пустой список
            queryset = Employee.objects.none()
        
        # Фильтрация по поисковому запросу
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(position__icontains=search)
            )
        
        # Фильтрация по должности
        position = self.request.query_params.get('position', None)
        if position and position != 'all':
            queryset = queryset.filter(position=position)
        
        # Фильтрация по статусу
        status_filter = self.request.query_params.get('status', None)
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        # Фильтрация по опыту работы
        experience = self.request.query_params.get('experience', None)
        if experience and experience != 'all':
            if experience == 'junior':
                queryset = queryset.filter(experience__lt=1)
            elif experience == 'middle':
                queryset = queryset.filter(experience__gte=1, experience__lte=3)
            elif experience == 'senior':
                queryset = queryset.filter(experience__gt=3)
        
        return queryset.order_by('-id')
    
    def perform_create(self, serializer):
        """
        При создании сотрудника создаем пользователя с ролью employee
        """
        user = self.request.user
        
        # Проверяем права доступа
        if user.role != User.Role.ADMIN or not user.business:
            raise PermissionDenied("Только администраторы могут создавать сотрудников")
        
        # Создаем пользователя для сотрудника
        employee_data = serializer.validated_data
        
        # Удаляем пробелы из номера телефона
        phone = employee_data['phone'].replace(' ', '')
        employee_data['phone'] = phone
        
        # Проверяем уникальность телефона
        if User.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError({
                'phone': 'Пользователь с таким номером телефона уже существует'
            })
        
        # Проверяем уникальность email (если указан)
        if employee_data.get('email') and User.objects.filter(email=employee_data['email']).exists():
            raise serializers.ValidationError({
                'email': 'Пользователь с таким email уже существует'
            })
        
        # Генерируем временный пароль
        import random
        import string
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        try:
            # Создаем пользователя
            new_user = User.objects.create_user(
                phone_number=phone,
                email=employee_data['email'],
                full_name=employee_data['name'],
                password=temp_password,
                role=User.Role.EMPLOYEE,
                business=user.business
            )
            
            # Сохраняем сотрудника с привязкой к пользователю и бизнесу
            employee = serializer.save(
                user=new_user,
                business=user.business
            )
            
            # Отправляем временный пароль через WhatsApp
            try:
                # Форматируем номер телефона для WhatsApp
                whatsapp_number = phone.replace('+', '')
                if not whatsapp_number.startswith('996'):
                    whatsapp_number = '996' + whatsapp_number
                
                # Формируем сообщение
                message = f"👋 Добро пожаловать в команду {user.business.name}!\n\n" \
                         f"🔐 Ваши данные для входа:\n" \
                         f"Логин: {phone}\n" \
                         f"Пароль: {temp_password}\n\n" \
                         f"🌐 Войти можно по ссылке: zappis.app/employee\n\n" \
                         f"⚠️ Рекомендуем сменить пароль после первого входа."
                
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
                    print(f"✅ WhatsApp с паролем отправлен сотруднику {employee.name} на {phone}")
                else:
                    print(f"❌ Ошибка отправки WhatsApp на {phone}: {response.text}")
                    print(f"Временный пароль для {employee.name}: {temp_password}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Ошибка подключения к WhatsApp API: {e}")
                print(f"Временный пароль для {employee.name}: {temp_password}")
            
            return employee
            
        except Exception as e:
            # Если что-то пошло не так, удаляем созданного пользователя
            if 'new_user' in locals():
                new_user.delete()
            raise e
    
    def perform_update(self, serializer):
        """
        При обновлении сотрудника обновляем данные пользователя
        """
        user = self.request.user
        employee = serializer.instance
        
        # Проверяем права доступа
        if user.role == User.Role.ADMIN:
            if user.business != employee.business:
                raise PermissionError("Нет прав для редактирования этого сотрудника")
        elif user.role == User.Role.EMPLOYEE:
            if user != employee.user:
                raise PermissionError("Нет прав для редактирования этого сотрудника")
        else:
            raise PermissionError("Недостаточно прав")
        
        # Обновляем данные пользователя
        if employee.user:
            employee_data = serializer.validated_data
            employee.user.full_name = employee_data.get('name', employee.user.full_name)
            employee.user.phone_number = employee_data.get('phone', employee.user.phone_number)
            employee.user.email = employee_data.get('email', employee.user.email)
            employee.user.save()
        
        return serializer.save()
    
    def perform_destroy(self, instance):
        """
        При удалении сотрудника деактивируем пользователя
        """
        user = self.request.user
        
        # Проверяем права доступа
        if user.role != User.Role.ADMIN or user.business != instance.business:
            raise PermissionError("Нет прав для удаления этого сотрудника")
        
        # Деактивируем пользователя
        if instance.user:
            instance.user.is_active = False
            instance.user.save()
        
        return super().perform_destroy(instance)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Получение статистики по сотрудникам (только для бизнеса пользователя)
        """
        user = self.request.user
        
        if user.role != User.Role.ADMIN or not user.business:
            return Response({'error': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        
        queryset = Employee.objects.filter(business=user.business)
        
        total_employees = queryset.count()
        active_employees = queryset.filter(status='active').count()
        vacation_employees = queryset.filter(status='vacation').count()
        sick_employees = queryset.filter(status='sick').count()
        
        # Статистика по должностям
        position_stats = queryset.values('position').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Средний рейтинг
        avg_rating = queryset.aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        # Общее количество клиентов
        total_clients = queryset.aggregate(
            total_clients=Sum('clientsCount')
        )['total_clients'] or 0
        
        return Response({
            'total_employees': total_employees,
            'active_employees': active_employees,
            'vacation_employees': vacation_employees,
            'sick_employees': sick_employees,
            'position_stats': list(position_stats),
            'avg_rating': round(avg_rating, 2),
            'total_clients': total_clients
        })
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Обновление статуса сотрудника
        """
        user = self.request.user
        employee = self.get_object()
        
        # Проверяем права доступа
        if user.role != User.Role.ADMIN or user.business != employee.business:
            return Response({'error': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        
        new_status = request.data.get('status')
        
        if new_status in ['active', 'inactive', 'vacation', 'sick']:
            employee.status = new_status
            employee.save()
            return Response({'status': 'success', 'message': 'Статус обновлен'})
        
        return Response(
            {'status': 'error', 'message': 'Неверный статус'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def add_performance_review(self, request, pk=None):
        """
        Добавление оценки работы сотрудника
        """
        user = self.request.user
        employee = self.get_object()
        
        # Проверяем права доступа
        if user.role != User.Role.ADMIN or user.business != employee.business:
            return Response({'error': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        
        review_data = request.data
        
        # Получаем текущие оценки
        reviews = employee.performanceReviews or []
        
        # Добавляем новую оценку
        new_review = {
            'date': review_data.get('date'),
            'rating': review_data.get('rating'),
            'comments': review_data.get('comments')
        }
        reviews.append(new_review)
        
        employee.performanceReviews = reviews
        employee.save()
        
        return Response({'status': 'success', 'message': 'Оценка добавлена'})
    
    @action(detail=True, methods=['post'])
    def add_training(self, request, pk=None):
        """
        Добавление записи об обучении сотрудника
        """
        user = self.request.user
        employee = self.get_object()
        
        # Проверяем права доступа
        if user.role != User.Role.ADMIN or user.business != employee.business:
            return Response({'error': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        
        training_data = request.data
        
        # Получаем текущую историю обучения
        training_history = employee.trainingHistory or []
        
        # Добавляем новую запись
        new_training = {
            'date': training_data.get('date'),
            'course': training_data.get('course'),
            'provider': training_data.get('provider')
        }
        training_history.append(new_training)
        
        employee.trainingHistory = training_history
        employee.save()
        
        return Response({'status': 'success', 'message': 'Обучение добавлено'})
    
    @action(detail=True, methods=['post'])
    def update_salary(self, request, pk=None):
        """
        Обновление зарплаты сотрудника с сохранением истории
        """
        user = self.request.user
        employee = self.get_object()
        
        # Проверяем права доступа
        if user.role != User.Role.ADMIN or user.business != employee.business:
            return Response({'error': 'Недостаточно прав'}, status=status.HTTP_403_FORBIDDEN)
        
        new_salary = request.data.get('salary')
        reason = request.data.get('reason', 'Изменение зарплаты')
        
        if new_salary:
            # Получаем текущую историю зарплат
            salary_history = employee.salaryHistory or []
            
            # Добавляем новую запись
            new_salary_record = {
                'date': request.data.get('date'),
                'amount': new_salary,
                'reason': reason
            }
            salary_history.append(new_salary_record)
            
            employee.salary = new_salary
            employee.salaryHistory = salary_history
            employee.save()
            
            return Response({'status': 'success', 'message': 'Зарплата обновлена'})
        
        return Response(
            {'status': 'error', 'message': 'Не указана новая зарплата'},
            status=status.HTTP_400_BAD_REQUEST
        )

# Дополнительные API endpoints для интеграции с фронтендом
def employee_list_api(request):
    """
    API endpoint для получения списка сотрудников (для совместимости с фронтендом)
    """
    if request.method == 'GET':
        user = request.user
        
        # Фильтруем по бизнесу пользователя
        if user.role == User.Role.ADMIN and user.business:
            employees = Employee.objects.filter(business=user.business)
        elif user.role == User.Role.EMPLOYEE:
            try:
                employees = Employee.objects.filter(user=user)
            except Employee.DoesNotExist:
                employees = Employee.objects.none()
        else:
            employees = Employee.objects.none()
        
        # Применяем фильтры
        search = request.GET.get('search')
        if search:
            employees = employees.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        
        position = request.GET.get('position')
        if position and position != 'all':
            employees = employees.filter(position=position)
        
        status_filter = request.GET.get('status')
        if status_filter and status_filter != 'all':
            employees = employees.filter(status=status_filter)
        
        # Сериализуем данные
        serializer = EmployeeSerializer(employees, many=True)
        return JsonResponse(serializer.data, safe=False)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def employee_detail_api(request, employee_id):
    """
    API endpoint для получения/обновления/удаления конкретного сотрудника
    """
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Сотрудник не найден'}, status=404)
    
    if request.method == 'GET':
        data = {
            'id': employee.id,
            'name': employee.name,
            'position': employee.position,
            'phone': employee.phone,
            'email': employee.email,
            'status': employee.status,
            'experience': employee.experience,
            'birthDate': employee.birthDate.isoformat() if employee.birthDate else None,
            'education': employee.education,
            'skills': employee.skills,
            'address': employee.address,
            'salary': employee.salary,
            'schedule': employee.schedule,
            'clientsCount': employee.clientsCount,
            'rating': employee.rating,
            'passportNumber': employee.passportNumber,
            'passportIssued': employee.passportIssued.isoformat() if employee.passportIssued else None,
            'passportExpiry': employee.passportExpiry.isoformat() if employee.passportExpiry else None,
            'taxId': employee.taxId,
            'bankAccount': employee.bankAccount,
            'bankName': employee.bankName,
            'emergencyContact': employee.emergencyContact,
            'emergencyContactName': employee.emergencyContactName,
            'emergencyContactRelation': employee.emergencyContactRelation,
            'startDate': employee.startDate.isoformat() if employee.startDate else None,
            'contractNumber': employee.contractNumber,
            'contractExpiry': employee.contractExpiry.isoformat() if employee.contractExpiry else None,
            'vacationDaysTotal': employee.vacationDaysTotal,
            'vacationDaysUsed': employee.vacationDaysUsed,
            'sickDaysTotal': employee.sickDaysTotal,
            'sickDaysUsed': employee.sickDaysUsed,
            'certifications': employee.certifications,
            'languages': employee.languages,
            'achievements': employee.achievements,
            'notes': employee.notes,
            'equipment': employee.equipment,
            'insuranceNumber': employee.insuranceNumber,
            'insuranceExpiry': employee.insuranceExpiry.isoformat() if employee.insuranceExpiry else None,
            'performanceReviews': employee.performanceReviews,
            'trainingHistory': employee.trainingHistory,
            'workSchedule': employee.workSchedule,
            'salaryHistory': employee.salaryHistory,
            'documents': employee.documents
        }
        return JsonResponse(data)
    
    elif request.method == 'PUT':
        # Обновление сотрудника
        try:
            data = request.POST.dict()
            
            # Обработка JSON полей
            for field in ['performanceReviews', 'trainingHistory', 'workSchedule', 'salaryHistory', 'documents']:
                if field in data and data[field]:
                    import json
                    data[field] = json.loads(data[field])
            
            # Обработка дат
            date_fields = ['birthDate', 'passportIssued', 'passportExpiry', 'startDate', 'contractExpiry', 'insuranceExpiry']
            for field in date_fields:
                if field in data and data[field]:
                    from datetime import datetime
                    data[field] = datetime.strptime(data[field], '%Y-%m-%d').date()
            
            # Обработка числовых полей
            numeric_fields = ['experience', 'salary', 'clientsCount', 'rating', 'vacationDaysTotal', 'vacationDaysUsed', 'sickDaysTotal', 'sickDaysUsed']
            for field in numeric_fields:
                if field in data and data[field]:
                    data[field] = int(data[field])
            
            for field, value in data.items():
                if hasattr(employee, field):
                    setattr(employee, field, value)
            
            employee.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Сотрудник обновлен успешно'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    elif request.method == 'DELETE':
        # Удаление сотрудника
        employee.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Сотрудник удален успешно'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Метод не поддерживается'}, status=405)

def api_test_view(request):
    """
    Тестовая страница для проверки API
    """
    return render(request, 'employees/employees.html')

class BusinessTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessType.objects.all()
    serializer_class = BusinessTypeSerializer

class BusinessSubtypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessSubtype.objects.all()
    serializer_class = BusinessSubtypeSerializer

class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

@require_GET
def positions_for_current_business(request):
    user = request.user
    if not user.is_authenticated or not hasattr(user, 'business') or not user.business or not user.business.subtype:
        return JsonResponse({'positions': []})
    positions = Position.objects.filter(business_subtype=user.business.subtype)
    data = [{'id': p.id, 'name': p.name} for p in positions]
    return JsonResponse({'positions': data})

def get_masters_api(request):
    user = request.user
    if not user.is_authenticated or not hasattr(user, 'business') or not user.business:
        return JsonResponse([], safe=False)
    masters = Employee.objects.filter(is_master=True, business=user.business).values('id', 'name', 'is_master')
    return JsonResponse(list(masters), safe=False)

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

def employees_page(request):
    lang = get_user_language(request)
    is_mob = is_mobile(request)
    template = f"employees/{lang}/employees_mobile.html" if is_mob else f"employees/{lang}/employees.html"
    return render(request, template, {"current_language": lang})

def edata_page(request):
    lang = get_user_language(request)
    is_mob = is_mobile(request)
    template = f"employees/{lang}/edata_mobile.html" if is_mob else f"employees/{lang}/edata.html"
    return render(request, template, {"current_language": lang})

# Обернуть все FBV
for fn in [employee_list_api, employee_detail_api, api_test_view, positions_for_current_business, get_masters_api, employees_page, edata_page]:
    globals()[fn.__name__] = admin_or_owner_required(fn)
