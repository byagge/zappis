from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.businesses.models import Business, BusinessType, BusinessSubtype
from apps.dashboard.models import BusinessStats, FinanceRecord, ActivityLog
from apps.clients.models import Client
from apps.services.models import Service, ServiceCategory
from apps.employees.models import Employee, Position
from apps.schedules.models import Booking
from apps.main.models import City
from decimal import Decimal
from datetime import timedelta, time
import random
from django.db.models import Sum, Avg

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает тестовые данные для dashboard'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных для dashboard...')

        # Создаем город если его нет
        city, created = City.objects.get_or_create(
            name='Бишкек',
            defaults={'name': 'Бишкек'}
        )

        # Создаем тип бизнеса
        business_type, created = BusinessType.objects.get_or_create(
            name='Красота и здоровье',
            defaults={'name': 'Красота и здоровье'}
        )

        # Создаем подтип бизнеса
        business_subtype, created = BusinessSubtype.objects.get_or_create(
            business_type=business_type,
            name='Салон красоты',
            defaults={'name': 'Салон красоты'}
        )

        # Создаем пользователя-владельца бизнеса
        owner, created = User.objects.get_or_create(
            phone_number='+996700123456',
            defaults={
                'full_name': 'Анна Иванова',
                'role': User.Role.ADMIN,
                'is_active': True,
                'is_phone_verified': True
            }
        )

        # Создаем бизнес
        business, created = Business.objects.get_or_create(
            name='Салон красоты "Элегант"',
            defaults={
                'description': 'Современный салон красоты в центре города',
                'type': business_type,
                'subtype': business_subtype,
                'employees_count': '5+',
                'owner': owner,
                'address': 'ул. Советская, 123',
                'city': city,
                'phone': '+996700123456',
                'email': 'elegant@example.com',
                'username': 'elegant_salon',
                'is_active': True
            }
        )

        # Создаем должности
        positions = []
        position_names = ['Мастер-стилист', 'Косметолог', 'Маникюрщица', 'Массажист']
        for pos_name in position_names:
            position, created = Position.objects.get_or_create(
                name=pos_name,
                business_subtype=business_subtype,
                defaults={'name': pos_name}
            )
            positions.append(position)

        # Создаем сотрудников
        employee_names = [
            'Елена Смирнова', 'Мария Козлова', 'Анна Петрова', 'Ольга Иванова',
            'Татьяна Сидорова', 'Ирина Волкова'
        ]
        
        employees = []
        for i, name in enumerate(employee_names):
            employee, created = Employee.objects.get_or_create(
                name=name,
                business=business,
                defaults={
                    'position': positions[i % len(positions)],
                    'phone': f'+996700{200000 + i}',
                    'email': f'employee{i}@elegant.com',
                    'status': 'active',
                    'experience': random.randint(2, 8),
                    'salary': random.randint(30000, 80000),
                    'is_master': True
                }
            )
            employees.append(employee)

        # Создаем категории услуг
        categories = []
        category_names = ['Стрижки', 'Окрашивание', 'Уход за лицом', 'Маникюр и педикюр']
        for cat_name in category_names:
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_name,
                business=business,
                defaults={'name': cat_name, 'description': f'Услуги категории {cat_name}'}
            )
            categories.append(category)

        # Создаем услуги
        services_data = [
            ('Стрижка женская', 2000, 60, 0),
            ('Стрижка мужская', 1500, 45, 0),
            ('Окрашивание волос', 5000, 120, 1),
            ('Мелирование', 4000, 90, 1),
            ('Укладка', 1500, 45, 0),
            ('Чистка лица', 3000, 60, 2),
            ('Массаж лица', 2500, 45, 2),
            ('Маникюр', 2000, 60, 3),
            ('Педикюр', 2500, 75, 3),
            ('Массаж тела', 4000, 90, 2)
        ]
        
        services = []
        for name, price, duration, cat_index in services_data:
            service, created = Service.objects.get_or_create(
                name=name,
                business=business,
                defaults={
                    'category': categories[cat_index],
                    'price': price,
                    'duration': duration,
                    'is_active': True
                }
            )
            services.append(service)

        # Создаем клиентов
        client_names = [
            'Мария Петрова', 'Анна Сидорова', 'Елена Козлова', 'Ольга Морозова',
            'Татьяна Волкова', 'Ирина Алексеева', 'Наталья Лебедева',
            'Светлана Соколова', 'Юлия Зайцева', 'Екатерина Павлова',
            'Ангелина Смирнова', 'Виктория Новикова', 'Дарья Федорова',
            'Алиса Морозова', 'Полина Алексеева'
        ]

        clients = []
        for i, name in enumerate(client_names):
            client, created = Client.objects.get_or_create(
                name=name,
                business=business,
                defaults={
                    'phone': f'+996700{100000 + i}',
                    'email': f'client{i}@example.com',
                    'status': random.choice(['new', 'regular', 'vip']),
                    'total_visits': random.randint(0, 20),
                    'total_spent': Decimal(str(random.randint(0, 50000)))
                }
            )
            clients.append(client)

        # Создаем записи за последние 30 дней
        time_slots = [
            time(9, 0), time(10, 0), time(11, 0), time(12, 0),
            time(13, 0), time(14, 0), time(15, 0), time(16, 0), time(17, 0)
        ]
        
        bookings_created = 0
        for i in range(30):
            date = timezone.now().date() - timedelta(days=i)
            
            # Создаем несколько записей на день
            daily_bookings = random.randint(3, 8)
            used_times = set()  # Для отслеживания использованных временных слотов
            
            for j in range(daily_bookings):
                client = random.choice(clients)
                service = random.choice(services)
                employee = random.choice(employees)
                
                # Выбираем свободное время
                available_times = [t for t in time_slots if t not in used_times]
                if not available_times:
                    continue
                    
                start_time = random.choice(available_times)
                used_times.add(start_time)
                
                # Вычисляем время окончания
                duration_minutes = service.duration or 60
                end_hour = start_time.hour + (duration_minutes // 60)
                end_minute = start_time.minute + (duration_minutes % 60)
                if end_minute >= 60:
                    end_hour += 1
                    end_minute -= 60
                end_time = time(end_hour, end_minute)
                
                # Проверяем, не существует ли уже такая запись
                existing_booking = Booking.objects.filter(
                    master=employee,
                    date=date,
                    start_time=start_time
                ).first()
                
                if not existing_booking:
                    try:
                        booking = Booking.objects.create(
                            client=client,
                            service=service,
                            master=employee,
                            date=date,
                            start_time=start_time,
                            end_time=end_time,
                            price=service.price
                        )
                        bookings_created += 1
                    except Exception as e:
                        # Пропускаем если не удалось создать запись
                        continue

        # Обновляем статистику клиентов
        for client in clients:
            client.total_visits = client.bookings.count()
            client.total_spent = client.bookings.aggregate(total=Sum('price'))['total'] or 0
            client.save()

        # Создаем статистику бизнеса
        total_revenue = Booking.objects.filter(service__business=business).aggregate(
            total=Sum('price')
        )['total'] or 0
        
        avg_ticket = Booking.objects.filter(service__business=business).aggregate(
            avg=Avg('price')
        )['avg'] or 0

        stats, created = BusinessStats.objects.get_or_create(
            business=business,
            defaults={
                'total_clients': len(clients),
                'total_appointments': bookings_created,
                'total_revenue': total_revenue,
                'avg_ticket': avg_ticket
            }
        )

        # Обновляем статистику если она уже существует
        if not created:
            stats.total_clients = len(clients)
            stats.total_appointments = bookings_created
            stats.total_revenue = total_revenue
            stats.avg_ticket = avg_ticket
            stats.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно созданы тестовые данные:\n'
                f'- Бизнес: {business.name}\n'
                f'- Сотрудников: {len(employees)}\n'
                f'- Клиентов: {len(clients)}\n'
                f'- Услуг: {len(services)}\n'
                f'- Записей: {bookings_created}\n'
                f'- Общий доход: ₽{total_revenue:,.0f}\n'
                f'- Средний чек: ₽{avg_ticket:,.0f}'
            )
        ) 