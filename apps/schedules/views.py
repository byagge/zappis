from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Booking
from .serializers import BookingSerializer
from django.views.generic import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.http import HttpRequest, HttpResponseRedirect
from apps.accounts.models import User
from apps.employees.views import get_user_language, is_mobile
import requests
import re

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

class BookingViewSet(AdminOrOwnerOnlyMixin, viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'business') or not user.business:
            return Booking.objects.none()
        return Booking.objects.filter(service__business=user.business).select_related('master', 'service')

    def create(self, request, *args, **kwargs):
        print('DEBUG POST DATA:', request.data)
        response = super().create(request, *args, **kwargs)
        print('DEBUG RESPONSE:', response.data if hasattr(response, 'data') else response)
        return response

    def update(self, request, *args, **kwargs):
        print('DEBUG PUT DATA:', request.data)
        response = super().update(request, *args, **kwargs)
        print('DEBUG RESPONSE:', response.data if hasattr(response, 'data') else response)
        return response

def booking_page(request: HttpRequest):
    lang = get_user_language(request)
    is_mob = is_mobile(request)
    template = f"schedules/{lang}/@booking.html" if is_mob else f"schedules/{lang}/booking.html"
    return render(request, template, {"current_language": lang})

booking_page = admin_or_owner_required(booking_page)

class SendWhatsAppMessageAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            phone = request.data.get('phone')
            message = request.data.get('message')
            
            if not phone or not message:
                return Response({
                    'error': 'Phone number and message are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Форматируем номер телефона для WhatsApp
            # Убираем все нецифровые символы
            clean_number = re.sub(r'\D', '', phone)
            
            # Если номер начинается с 996, оставляем как есть
            if clean_number.startswith('996'):
                whatsapp_number = clean_number
            # Если номер начинается с 0, заменяем на 996
            elif clean_number.startswith('0'):
                whatsapp_number = '996' + clean_number[1:]
            # Если номер 9 цифр (без кода страны), добавляем 996
            elif len(clean_number) == 9:
                whatsapp_number = '996' + clean_number
            # Если номер 10 цифр (с кодом страны), добавляем 996
            elif len(clean_number) == 10:
                whatsapp_number = '996' + clean_number
            else:
                whatsapp_number = clean_number
            
            # Отправляем сообщение через WhatsApp API
            response = requests.post(
                'http://localhost:3000/send',
                json={
                    'number': whatsapp_number,
                    'message': message
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return Response({
                    'status': 'success',
                    'message': 'WhatsApp message sent successfully',
                    'original_number': phone,
                    'formatted_number': whatsapp_number
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': f'WhatsApp API error: {response.text}',
                    'status_code': response.status_code
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except requests.exceptions.RequestException as e:
            return Response({
                'error': f'Connection error to WhatsApp API: {str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                'error': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendReminderAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            booking_id = request.data.get('booking_id')
            hours_before = request.data.get('hours_before', 24)  # По умолчанию за 24 часа
            
            if not booking_id:
                return Response({'error': 'ID записи обязателен'}, status=status.HTTP_400_BAD_REQUEST)
            
            booking = get_object_or_404(Booking, id=booking_id)
            
            # Проверяем права доступа
            user = request.user
            if user.role != User.Role.ADMIN or user.business != booking.service.business:
                return Response({'error': 'Нет прав для отправки уведомлений'}, status=status.HTTP_403_FORBIDDEN)
            
            # Отправляем напоминание
            from .signals import send_custom_reminder
            
            success = send_custom_reminder(booking_id, hours_before)
            
            if success:
                time_text = "за день" if hours_before == 24 else f"за {hours_before} часа" if hours_before == 2 else f"за {hours_before} часов"
                return Response({
                    'success': True,
                    'message': f'Напоминание {time_text} отправлено клиенту'
                })
            else:
                return Response({
                    'error': 'Ошибка отправки напоминания'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'error': 'Произошла ошибка при отправке напоминания'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
