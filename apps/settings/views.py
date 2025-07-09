from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import (
    UserProfileSerializer, BusinessSettingsSerializer, 
    UserNotificationSettingsSerializer, BusinessNotificationSettingsSerializer,
    BookingSettingsSerializer, UserPreferencesSerializer
)
from apps.accounts.models import User
from apps.businesses.models import Business
from .models import UserNotificationSettings, BusinessNotificationSettings, BookingSettings, UserPreferences
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from apps.employees.views import get_user_language, is_mobile
import requests
import re
import random

# Create your views here. 

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

class SettingsProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SettingsBusinessAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        business = getattr(user, 'business', None)
        if not business:
            return Response({'detail': 'Бизнес не найден'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BusinessSettingsSerializer(business)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        business = getattr(user, 'business', None)
        if not business:
            return Response({'detail': 'Бизнес не найден'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BusinessSettingsSerializer(business, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserNotificationSettingsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        settings, created = UserNotificationSettings.objects.get_or_create(user=user)
        serializer = UserNotificationSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        settings, created = UserNotificationSettings.objects.get_or_create(user=user)
        serializer = UserNotificationSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BusinessNotificationSettingsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        business = getattr(user, 'business', None)
        if not business:
            return Response({'detail': 'Бизнес не найден'}, status=status.HTTP_404_NOT_FOUND)
        settings, created = BusinessNotificationSettings.objects.get_or_create(business=business)
        serializer = BusinessNotificationSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        business = getattr(user, 'business', None)
        if not business:
            return Response({'detail': 'Бизнес не найден'}, status=status.HTTP_404_NOT_FOUND)
        settings, created = BusinessNotificationSettings.objects.get_or_create(business=business)
        serializer = BusinessNotificationSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookingSettingsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        business = getattr(user, 'business', None)
        if not business:
            return Response({'detail': 'Бизнес не найден'}, status=status.HTTP_404_NOT_FOUND)
        settings, created = BookingSettings.objects.get_or_create(business=business)
        serializer = BookingSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        business = getattr(user, 'business', None)
        if not business:
            return Response({'detail': 'Бизнес не найден'}, status=status.HTTP_404_NOT_FOUND)
        settings, created = BookingSettings.objects.get_or_create(business=business)
        serializer = BookingSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserPreferencesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        serializer = UserPreferencesSerializer(preferences, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Пароли не совпадают.'})
        return data

class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Старый пароль неверный.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        # Удаляем все сессии пользователя (logout everywhere)
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        count = 0
        for session in sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(user.id):
                session.delete()
                count += 1
        # Если используется DRF Token
        if hasattr(user, 'auth_token'):
            user.auth_token.delete()
        return Response({'detail': 'Пароль успешно изменён. Выход выполнен на всех устройствах.'}, status=status.HTTP_200_OK)

@login_required
def settings_auto_view(request):
    lang = get_user_language(request)
    is_mob = is_mobile(request)
    template = f"settings/{lang}/settings_mobile.html" if is_mob else f"settings/{lang}/settings.html"
    user = request.user
    is_tarifed = getattr(user, 'is_tarifed', True)
    is_trial = getattr(user, 'is_trial', False)
    return render(request, template, {"current_language": lang, "is_tarifed": is_tarifed, "is_trial": is_trial})

class SendPhoneVerificationCodeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            phone = request.data.get('phone')
            if not phone:
                return Response({'error': 'Номер телефона обязателен'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Очищаем номер от пробелов и форматируем
            clean_phone = re.sub(r'\D', '', phone)
            if clean_phone.startswith('996'):
                clean_phone = clean_phone[3:]
            
            if len(clean_phone) != 9:
                return Response({'error': 'Неверный формат номера телефона'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Генерируем код подтверждения
            verification_code = str(random.randint(1000, 9999))
            
            # Формируем сообщение
            message = f"🔐 Код подтверждения Zappis: {verification_code}\n\n" \
                     f"Введите этот код для подтверждения номера телефона.\n" \
                     f"Код действителен в течение 10 минут.\n\n" \
                     f"Если вы не запрашивали этот код, проигнорируйте сообщение."
            
            # Отправляем через WhatsApp API
            whatsapp_url = "http://localhost:3000/send"
            payload = {
                "number": f"996{clean_phone}",
                "message": message
            }
            
            response = requests.post(whatsapp_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                # Сохраняем код в сессии для проверки
                request.session['phone_verification_code'] = verification_code
                request.session['phone_verification_number'] = f"996{clean_phone}"
                request.session['phone_verification_time'] = timezone.now().timestamp()
                
                return Response({
                    'success': True,
                    'message': 'Код подтверждения отправлен на WhatsApp'
                })
            else:
                return Response({
                    'error': 'Ошибка отправки кода. Попробуйте позже.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except requests.exceptions.RequestException:
            return Response({
                'error': 'WhatsApp сервер недоступен. Попробуйте позже.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                'error': 'Произошла ошибка при отправке кода.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyPhoneCodeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            code = request.data.get('code')
            if not code:
                return Response({'error': 'Код подтверждения обязателен'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем сохраненный код из сессии
            saved_code = request.session.get('phone_verification_code')
            saved_number = request.session.get('phone_verification_number')
            saved_time = request.session.get('phone_verification_time')
            
            if not saved_code or not saved_number or not saved_time:
                return Response({'error': 'Код подтверждения не найден. Запросите новый код.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем время действия кода (10 минут)
            current_time = timezone.now().timestamp()
            if current_time - saved_time > 600:  # 10 минут
                # Удаляем устаревший код
                del request.session['phone_verification_code']
                del request.session['phone_verification_number']
                del request.session['phone_verification_time']
                return Response({'error': 'Код подтверждения истек. Запросите новый код.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем код
            if code == saved_code:
                # Код верный, обновляем номер телефона пользователя
                user = request.user
                user.phone_number = saved_number
                user.save()
                
                # Удаляем код из сессии
                del request.session['phone_verification_code']
                del request.session['phone_verification_number']
                del request.session['phone_verification_time']
                
                return Response({
                    'success': True,
                    'message': 'Номер телефона успешно подтвержден'
                })
            else:
                return Response({'error': 'Неверный код подтверждения'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': 'Произошла ошибка при проверке кода.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Обернуть все CBV ---
for cls in [SettingsProfileAPIView, SettingsBusinessAPIView, UserNotificationSettingsAPIView, BusinessNotificationSettingsAPIView, BookingSettingsAPIView, UserPreferencesAPIView, ChangePasswordAPIView]:
    cls.dispatch = method_decorator(admin_or_owner_required)(cls.dispatch)

# --- Обернуть FBV ---
settings_auto_view = admin_or_owner_required(settings_auto_view) 