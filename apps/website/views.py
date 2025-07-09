from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta, time
from .models import Website, WebsiteBooking
from apps.businesses.models import Business
from apps.services.models import Service, ServiceCategory
from apps.employees.models import Employee
from apps.schedules.models import Booking
from apps.clients.models import Client
import json

def get_user_language(request):
    lang = request.GET.get('lang')
    if lang in ['ky', 'ru']:
        return lang
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    if accept.lower().startswith('ky'):
        return 'ky'
    return 'ru'

def public_website(request, username):
    """Публичный сайт бизнеса с поддержкой языка (ru/ky)"""
    website = get_object_or_404(Website, url=username)
    lang = get_user_language(request)
    template = f"ky/website.html" if lang == 'ky' else "ru/website.html"
    return render(request, template, {'website_url': username, 'current_language': lang})

@csrf_exempt
@require_http_methods(["GET"])
def get_website_data(request, username):
    """Получить данные сайта"""
    website = get_object_or_404(Website, url=username)
    business = website.business
    
    # Получаем данные бизнеса как словарь
    business_data = {
        'id': business.id,
        'name': business.name,
        'description': business.description or '',
        'address': business.address or '',
        'phone': business.phone or '',
        'email': business.email or '',
        'website': business.website_url or '',
        'instagram': business.instagram or '',
    }
    
    data = {
        'business_id': business_data['id'],
        'business_name': business_data['name'],
        'business_description': business_data['description'],
        'business_address': business_data['address'],
        'business_phone': business_data['phone'],
        'business_email': business_data['email'],
        'business_website': business_data['website'],
        'business_instagram': business_data['instagram'],
        'views_count': website.views_count,
        'bookings_count': website.bookings_count
    }
    return JsonResponse(data)

@csrf_exempt
@require_http_methods(["GET"])
def get_services(request, username):
    """Получить услуги и категории бизнеса"""
    business = get_object_or_404(Business, username=username)
    
    categories = ServiceCategory.objects.filter(business=business).values('id', 'name')
    services = Service.objects.filter(business=business, is_active=True).values(
        'id', 'name', 'category_id', 'price', 'duration'
    )
    
    # Форматируем данные для фронтенда
    formatted_services = []
    for service in services:
        duration_minutes = service['duration'] or 0
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        
        if hours > 0:
            if minutes > 0:
                duration = f"{hours} ч {minutes} мин"
            else:
                duration = f"{hours} ч"
        else:
            duration = f"{minutes} мин"
        
        price = f"{service['price']:,} сом" if service['price'] else "Не указана"
        
        formatted_services.append({
            'id': service['id'],
            'name': service['name'],
            'category': service['category_id'],
            'duration': duration,
            'price': price
        })
    
    data = {
        'categories': list(categories),
        'services': formatted_services
    }
    return JsonResponse(data)

@csrf_exempt
@require_http_methods(["GET"])
def get_employees(request, username):
    """Получить сотрудников бизнеса"""
    business = get_object_or_404(Business, username=username)
    
    employees = Employee.objects.filter(business=business, status='active').values(
        'id', 'name', 'position__name', 'rating'
    )
    
    # Получаем сегодняшнюю дату
    today = timezone.now().date()
    
    # Генерируем рабочие часы с шагом в 1 час
    working_hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00']
    
    formatted_employees = []
    for employee in employees:
        # Получаем записи мастера на сегодня
        today_bookings = Booking.objects.filter(
            master_id=employee['id'],
            date=today
        )
        
        # Определяем занятые времена
        booked_times = set()
        for booking in today_bookings:
            start_time = booking.start_time.strftime('%H:%M')
            end_time = booking.end_time.strftime('%H:%M')
            
            # Добавляем все времена между началом и концом
            current_time = datetime.strptime(start_time, '%H:%M')
            end_datetime = datetime.strptime(end_time, '%H:%M')
            
            while current_time < end_datetime:
                booked_times.add(current_time.strftime('%H:%M'))
                current_time += timedelta(hours=1)
        
        # Фильтруем доступные времена
        available_times = [time for time in working_hours if time not in booked_times]
        
        formatted_employees.append({
            'id': employee['id'],
            'name': employee['name'],
            'role': employee['position__name'] or 'Специалист',
            'rating': employee['rating'],
            'available_times': available_times
        })
    
    return JsonResponse(formatted_employees, safe=False)

@csrf_exempt
@require_http_methods(["GET"])
def get_schedule(request, username):
    """Получить расписание для сотрудника на определенную дату"""
    business = get_object_or_404(Business, username=username)
    
    employee_id = request.GET.get('employee_id')
    date_str = request.GET.get('date')
    
    if not date_str:
        return JsonResponse({'error': 'Date parameter required'}, status=400)
    
    if not employee_id:
        return JsonResponse({'error': 'Employee ID required'}, status=400)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Получаем записи на эту дату для конкретного сотрудника
    bookings = Booking.objects.filter(
        master_id=employee_id,
        date=date
    )
    
    # Генерируем доступные временные слоты с шагом в 1 час
    working_hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00']
    
    # Убираем занятые времена
    booked_times = set()
    for booking in bookings:
        start_time = booking.start_time.strftime('%H:%M')
        end_time = booking.end_time.strftime('%H:%M')
        current_time = datetime.strptime(start_time, '%H:%M')
        end_datetime = datetime.strptime(end_time, '%H:%M')
        while current_time < end_datetime:
            booked_times.add(current_time.strftime('%H:%M'))
            current_time += timedelta(hours=1)
    
    available_times = [time for time in working_hours if time not in booked_times]
    
    # Фильтруем времена в прошлом, если выбранная дата сегодня
    now = timezone.localtime().time() if date == timezone.localdate() else None
    if now:
        available_times = [t for t in available_times if datetime.strptime(t, '%H:%M').time() > now]
    
    # Если нет доступных времен, ищем ближайшее доступное время в будущем
    next_time = None
    if not available_times:
        search_date = date + timedelta(days=1)
        for _ in range(14):  # ищем максимум 2 недели вперед
            future_bookings = Booking.objects.filter(master_id=employee_id, date=search_date)
            booked_times = set()
            for booking in future_bookings:
                start_time = booking.start_time.strftime('%H:%M')
                end_time = booking.end_time.strftime('%H:%M')
                current_time = datetime.strptime(start_time, '%H:%M')
                end_datetime = datetime.strptime(end_time, '%H:%M')
                while current_time < end_datetime:
                    booked_times.add(current_time.strftime('%H:%M'))
                    current_time += timedelta(hours=1)
            future_available = [t for t in working_hours if t not in booked_times]
            if future_available:
                next_time = {'date': search_date.strftime('%Y-%m-%d'), 'time': future_available[0]}
                break
            search_date += timedelta(days=1)
    
    data = {
        'date': date_str,
        'employee_id': employee_id,
        'available_times': available_times,
        'next_available': next_time
    }
    
    return JsonResponse(data)

@csrf_exempt
@require_http_methods(["POST"])
def increment_views(request, username):
    """Увеличить счетчик просмотров"""
    website = get_object_or_404(Website, url=username)
    website.views_count += 1
    website.save()
    return JsonResponse({'success': True, 'views_count': website.views_count})

@csrf_exempt
@require_http_methods(["POST"])
def create_booking(request, username):
    """Создать бронирование"""
    website = get_object_or_404(Website, url=username)
    
    try:
        data = json.loads(request.body)
        booking = WebsiteBooking.objects.create(
            website=website,
            customer_name=data.get('customer_name', ''),
            customer_phone=data.get('customer_phone', ''),
            customer_email=data.get('customer_email', ''),
            service=data.get('service', ''),
            specialist=data.get('specialist', ''),
            date=data.get('date', ''),
            time=data.get('time', ''),
            comment=data.get('comment', '')
        )
        
        # Увеличиваем счетчики
        website.website_bookings_count += 1
        website.bookings_count += 1
        website.save()
        
        return JsonResponse({'success': True, 'booking_id': booking.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def create_test_booking(request, username):
    """Создать тестовую запись для отладки"""
    try:
        business = get_object_or_404(Business, username=username)
        
        # Получаем первого сотрудника
        employee = Employee.objects.filter(business=business).first()
        if not employee:
            return JsonResponse({'error': 'No employees found'}, status=400)
        
        # Получаем первую услугу
        service = Service.objects.filter(business=business).first()
        if not service:
            return JsonResponse({'error': 'No services found'}, status=400)
        
        # Получаем или создаем тестового клиента
        client, created = Client.objects.get_or_create(
            name="Тестовый клиент",
            defaults={'phone': '+996700000000'}
        )
        
        # Создаем тестовую запись на сегодня с 10:00 до 12:00
        booking = Booking.objects.create(
            client=client,
            service=service,
            master=employee,
            date=timezone.now().date(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            price=1000
        )
        
        return JsonResponse({
            'success': True, 
            'booking_id': booking.id,
            'message': f'Test booking created: {booking.start_time} - {booking.end_time}'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
