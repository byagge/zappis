from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import Step1Serializer, Step2Serializer, Step3Serializer, UserSerializer, VerifyCodeSerializer, UserSignUpSerializer, UserLanguageSerializer
from .models import RegistrationSession, User
from .utils import send_sms
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.generic import TemplateView
from django.utils.crypto import get_random_string
from apps.main.models import City
from apps.businesses.models import Business, BusinessType, BusinessSubtype
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model, login
from django.http import HttpRequest
from rest_framework_simplejwt.authentication import JWTAuthentication
import requests
from django.urls import reverse_lazy
from django.shortcuts import redirect
import re

class SignUpPageView(TemplateView):
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('dashboard-page')  # если используется CreateView

    def post(self, request, *args, **kwargs):
        # Если используется TemplateView с кастомной обработкой POST
        # Здесь должна быть логика создания пользователя
        # После успешной регистрации:
        return redirect('/dashboard/')

class UserSignUpAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserSignUpSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterPageView(TemplateView):
    template_name = 'accounts/register.html'

    def get_client_ip(self, request: HttpRequest):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_city_by_ip(self, ip):
        # Пример с abstractapi, замените на свой сервис и ключ
        try:
            resp = requests.get(f'https://ipgeolocation.abstractapi.com/v1/?api_key=YOUR_API_KEY&ip_address={ip}', timeout=2)
            data = resp.json()
            city_name = data.get('city')
            if city_name:
                city_obj = City.objects.filter(name__iexact=city_name).first()
                if city_obj:
                    return city_obj
        except Exception:
            pass
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        selected_city = None
        selected_country = None

        if user.is_authenticated and getattr(user, 'city', None):
            selected_city = user.city
            selected_country = user.country
        else:
            ip = self.get_client_ip(self.request)
            city_by_ip = self.get_city_by_ip(ip)
            # Проверяем, что city_by_ip реально есть в БД
            if city_by_ip and City.objects.filter(id=city_by_ip.id).exists():
                selected_city = city_by_ip
                selected_country = city_by_ip.country
            else:
                selected_city = City.objects.filter(country='KG').order_by('id').first()
                selected_country = selected_city.country if selected_city else 'Кыргызстан'

        cities = City.objects.filter(country='KG').order_by('name')
        cities_data = [{'id': city.id, 'name': city.name} for city in cities]
        
        # Получаем типы бизнеса из базы данных
        business_types = BusinessType.objects.all().order_by('name')
        business_types_data = [{'id': bt.id, 'name': bt.name} for bt in business_types]
        
        context['selected_city'] = selected_city
        context['selected_country'] = selected_country
        context['cities'] = cities_data
        context['business_types'] = business_types_data
        return context

class Step1View(APIView):
    def post(self, request):
        ser = Step1Serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # Нормализация телефона
        phone = data['phone']
        if not phone.startswith('+996'):
            phone = '+996' + phone

        session = RegistrationSession.objects.create(
            full_name=data['full_name'],
            phone=phone,
            country=data['country'],
            city=City.objects.get(id=data['city']),
            agree_to_terms=data['agree_to_terms'],
        )
        send_sms(phone)
        return Response({'registration_id': session.id, 'next_step': 2}, status=status.HTTP_201_CREATED)

class Step2View(APIView):
    def post(self, request):
        ser = Step2Serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        session = RegistrationSession.objects.get(id=data['registration_id'])
        session.company_name = data['company_name']
        session.business_type = data['business_type']
        session.business_subtype = data['business_subtype']
        session.employees_count = data['employees_count']
        session.save()
        return Response({'registration_id': session.id, 'next_step': 3})

class Step3View(APIView):
    def post(self, request):
        ser = Step3Serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        session = RegistrationSession.objects.get(id=data['registration_id'])
        if not session.check_code(data['code']):
            return Response({'detail': 'Неверный код'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем объект города
        city_obj = session.city
        if not city_obj:
            return Response({'detail': 'Город не найден (city_obj is None)'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем объекты типа и подтипа бизнеса (если указаны)
        business_type_obj = session.business_type
        business_subtype_obj = session.business_subtype

        now = timezone.now()
        ip = request.META.get('REMOTE_ADDR')
        device = request.META.get('HTTP_USER_AGENT', '')

        with transaction.atomic():
            UserModel = get_user_model()
            user = UserModel(
                email=None,
                full_name=session.full_name,
                phone_number=session.phone,
                city=city_obj,
                country=session.country,
                last_login_time=now,
                last_login_ip=ip,
                last_login_device=device,
                last_login_device_time=now,
                role=UserModel.Role.ADMIN
            )
            user.set_password(data['password'])
            user.save()  # Сначала сохраняем пользователя

            user_id_str = str(user.id)
            if hasattr(user.id, 'hex'):
                user_id_short = user.id.hex[:8]
            else:
                user_id_short = user_id_str[:8]

            business_kwargs = dict(
                name=session.company_name or '',
                employees_count=session.employees_count or '',
                city=city_obj,
                country=session.country,
                owner=user,
                username=f'biz_{user_id_short}'
            )
            if business_type_obj:
                business_kwargs['type'] = business_type_obj
            if business_subtype_obj:
                business_kwargs['subtype'] = business_subtype_obj

            business = Business(**business_kwargs)
            business.save()

            user.business = business
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'user': UserSerializer(user).data
        })

class VerifyCodeView(APIView):
    def post(self, request):
        ser = VerifyCodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        
        try:
            session = RegistrationSession.objects.get(id=data['registration_id'])
            if session.check_code(data['code']):
                return Response({'detail': 'Код верный'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Неверный код'}, status=status.HTTP_400_BAD_REQUEST)
        except RegistrationSession.DoesNotExist:
            return Response({'detail': 'Сессия регистрации не найдена'}, status=status.HTTP_404_NOT_FOUND)

class ResendCodeView(APIView):
    def post(self, request):
        registration_id = request.data.get('registration_id')
        if not registration_id:
            return Response({'detail': 'registration_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            session = RegistrationSession.objects.get(id=registration_id)
            # Генерируем новый код и отправляем через WhatsApp
            new_code = send_sms(session.phone)
            return Response({
                'detail': 'Новый код отправлен в WhatsApp',
                'phone': session.phone
            }, status=status.HTTP_200_OK)
        except RegistrationSession.DoesNotExist:
            return Response({'detail': 'Сессия регистрации не найдена'}, status=status.HTTP_404_NOT_FOUND)

class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'id': str(user.id),
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'email': user.email,
            'role': user.role,
            'business': {
                'id': user.business.id,
                'name': user.business.name,
                'username': user.business.username
            } if user.business else None,
            'city': {
                'id': user.city.id,
                'name': user.city.name
            } if user.city else None,
            'country': user.country,
            'is_active': user.is_active,
            'date_joined': user.date_joined
        })

class UserLanguageUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        serializer = UserLanguageSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'preferred_language': serializer.data['preferred_language']})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateSessionAPIView(APIView):
    """Создает Django сессию для пользователя с JWT токеном"""
    permission_classes = [permissions.AllowAny]
    authentication_classes = [JWTAuthentication]

    def post(self, request, *args, **kwargs):
        try:
            # Получаем пользователя из JWT токена
            user = request.user
            if not user.is_authenticated:
                return Response({'error': 'Неверный токен'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Создаем Django сессию
            login(request, user)
            
            return Response({
                'message': 'Сессия создана успешно',
                'user_id': user.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SimpleRegisterAPIView(APIView):
    """
    Простой API для регистрации пользователей
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            # Получаем данные из запроса
            full_name = request.data.get('full_name')
            phone = request.data.get('phone')
            company_name = request.data.get('company_name')
            business_type = request.data.get('business_type')
            password = request.data.get('password')
            agree_to_terms = request.data.get('agree_to_terms')

            # Валидация обязательных полей
            if not all([full_name, phone, company_name, business_type, password, agree_to_terms]):
                return Response({
                    'detail': 'Все поля обязательны для заполнения'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not agree_to_terms:
                return Response({
                    'detail': 'Необходимо согласие с условиями'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Нормализация телефона
            phone_digits = re.sub(r'\D', '', phone)
            if phone_digits.startswith('996'):
                phone_digits = phone_digits[3:]
            if len(phone_digits) != 9:
                return Response({
                    'detail': 'Неверный формат номера телефона'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            normalized_phone = f"+996{phone_digits}"

            # Проверяем, не существует ли уже пользователь с таким телефоном
            if User.objects.filter(phone_number=normalized_phone).exists():
                return Response({
                    'detail': 'Пользователь с таким номером телефона уже существует'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Получаем город по умолчанию (Бишкек)
            default_city = City.objects.filter(country='KG').first()
            if not default_city:
                return Response({
                    'detail': 'Ошибка конфигурации: город не найден'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Получаем тип бизнеса
            try:
                business_type_obj = BusinessType.objects.get(id=business_type)
            except BusinessType.DoesNotExist:
                return Response({
                    'detail': 'Неверный тип бизнеса'
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Создаем пользователя
                UserModel = get_user_model()
                user = UserModel(
                    full_name=full_name,
                    phone_number=normalized_phone,
                    city=default_city,
                    country='Кыргызстан',
                    role=UserModel.Role.ADMIN,
                    is_phone_verified=True  # Пока отключаем верификацию
                )
                user.set_password(password)
                user.save()

                # Создаем бизнес
                user_id_str = str(user.id)
                if hasattr(user.id, 'hex'):
                    user_id_short = user.id.hex[:8]
                else:
                    user_id_short = user_id_str[:8]

                business = Business.objects.create(
                    name=company_name,
                    type=business_type_obj,
                    city=default_city,
                    country='Кыргызстан',
                    owner=user,
                    username=f'biz_{user_id_short}'
                )

                # Связываем пользователя с бизнесом
                user.business = business
                user.save()

                # Создаем JWT токен
                refresh = RefreshToken.for_user(user)

                return Response({
                    'token': str(refresh.access_token),
                    'user': {
                        'id': str(user.id),
                        'full_name': user.full_name,
                        'phone_number': user.phone_number,
                        'business': {
                            'id': business.id,
                            'name': business.name
                        }
                    },
                    'message': 'Регистрация успешно завершена'
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'detail': f'Ошибка при регистрации: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BusinessTypesAPIView(APIView):
    """
    API для получения списка типов бизнеса
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            business_types = BusinessType.objects.all().order_by('name')
            data = [{'id': bt.id, 'name': bt.name} for bt in business_types]
            
            return Response({
                'business_types': data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'detail': f'Ошибка при получении типов бизнеса: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
