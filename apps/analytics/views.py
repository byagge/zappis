from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import datetime, timedelta
from .models import AnalyticsReport, AnalyticsDashboard, AnalyticsMetric, AnalyticsService
from .serializers import (
    AnalyticsReportSerializer, AnalyticsDashboardSerializer, AnalyticsMetricSerializer,
    RevenueDataSerializer, ClientsDataSerializer, ServicesDataSerializer,
    EmployeesDataSerializer, BookingsDataSerializer, DashboardSummarySerializer,
    ChartDataSerializer, AnalyticsFilterSerializer
)
from apps.clients.models import Client
from apps.schedules.models import Booking
from apps.services.models import Service
from apps.employees.models import Employee
from django.db.models import Sum, Count, Avg, Q
import json

class AnalyticsPageView(TemplateView):
    """Представление для страницы аналитики"""
    template_name = 'analytics/analytics.html'

class DashboardSummaryAPIView(APIView):
    """API для получения сводки дашборда"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not user.business:
            return Response({'error': 'У вас нет привязанного бизнеса'}, status=400)
        
        analytics_service = AnalyticsService(user.business)
        summary = analytics_service.get_dashboard_summary()
        
        serializer = DashboardSummarySerializer(summary)
        return Response(serializer.data)

class RevenueDataAPIView(APIView):
    """API для получения данных о выручке"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not user.business:
            return Response({'error': 'У вас нет привязанного бизнеса'}, status=400)
        
        # Получаем параметры фильтрации
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        period = request.GET.get('period', 'daily')
        
        # Если даты не указаны, используем текущий месяц
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics_service = AnalyticsService(user.business)
        revenue_data = analytics_service.get_revenue_data(start_date, end_date, period)
        
        # Форматируем данные для графика
        labels = []
        revenue_values = []
        bookings_values = []
        
        for item in revenue_data:
            if period == 'daily':
                labels.append(item['date'].strftime('%d.%m'))
            elif period == 'weekly':
                labels.append(f'Неделя {item["week"]}')
            elif period == 'monthly':
                labels.append(f'{item["month"]}.{item["year"]}')
            
            revenue_values.append(float(item['revenue']))
            bookings_values.append(item['bookings_count'])
        
        chart_data = {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Выручка',
                    'data': revenue_values,
                    'borderColor': 'rgb(59, 130, 246)',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'yAxisID': 'y'
                },
                {
                    'label': 'Количество записей',
                    'data': bookings_values,
                    'borderColor': 'rgb(34, 197, 94)',
                    'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                    'yAxisID': 'y1'
                }
            ]
        }
        
        return Response(chart_data)

class ClientsDataAPIView(APIView):
    """API для получения данных о клиентах"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not user.business:
            return Response({'error': 'У вас нет привязанного бизнеса'}, status=400)
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics_service = AnalyticsService(user.business)
        clients_data = analytics_service.get_clients_data(start_date, end_date)
        
        # Получаем данные по дням для графика
        clients = Client.objects.filter(business=user.business)
        daily_data = []
        
        current_date = start_date
        while current_date <= end_date:
            daily_clients = clients.filter(created_at__date=current_date).count()
            daily_data.append({
                'date': current_date.strftime('%d.%m'),
                'count': daily_clients
            })
            current_date += timedelta(days=1)
        
        chart_data = {
            'summary': clients_data,
            'daily_data': daily_data
        }
        
        return Response(chart_data)

class ServicesDataAPIView(APIView):
    """API для получения данных об услугах"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not user.business:
            return Response({'error': 'У вас нет привязанного бизнеса'}, status=400)
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics_service = AnalyticsService(user.business)
        services_data = analytics_service.get_services_data(start_date, end_date)
        
        # Форматируем данные для круговой диаграммы
        labels = []
        revenue_values = []
        colors = [
            '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
            '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6366F1'
        ]
        
        for i, item in enumerate(services_data):
            labels.append(item['service__name'])
            revenue_values.append(float(item['total_revenue']))
        
        chart_data = {
            'labels': labels,
            'datasets': [{
                'data': revenue_values,
                'backgroundColor': colors[:len(labels)],
                'borderWidth': 2,
                'borderColor': '#ffffff'
            }]
        }
        
        return Response({
            'chart_data': chart_data,
            'services_data': services_data
        })

class EmployeesDataAPIView(APIView):
    """API для получения данных о сотрудниках"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not user.business:
            return Response({'error': 'У вас нет привязанного бизнеса'}, status=400)
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics_service = AnalyticsService(user.business)
        employees_data = analytics_service.get_employees_data(start_date, end_date)
        
        # Форматируем данные для столбчатой диаграммы
        labels = []
        revenue_values = []
        bookings_values = []
        
        for item in employees_data:
            labels.append(item['employee__name'])
            revenue_values.append(float(item['total_revenue']))
            bookings_values.append(item['bookings_count'])
        
        chart_data = {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Выручка',
                    'data': revenue_values,
                    'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                    'borderColor': 'rgb(59, 130, 246)',
                    'borderWidth': 1
                },
                {
                    'label': 'Количество записей',
                    'data': bookings_values,
                    'backgroundColor': 'rgba(34, 197, 94, 0.8)',
                    'borderColor': 'rgb(34, 197, 94)',
                    'borderWidth': 1
                }
            ]
        }
        
        return Response({
            'chart_data': chart_data,
            'employees_data': employees_data
        })

class BookingsDataAPIView(APIView):
    """API для получения данных о записях"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not user.business:
            return Response({'error': 'У вас нет привязанного бизнеса'}, status=400)
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics_service = AnalyticsService(user.business)
        bookings_data = analytics_service.get_bookings_data(start_date, end_date)
        
        # Получаем данные по дням для графика
        bookings = Booking.objects.filter(business=user.business, date__range=[start_date, end_date])
        daily_data = []
        
        current_date = start_date
        while current_date <= end_date:
            daily_bookings = bookings.filter(date=current_date).count()
            daily_completed = bookings.filter(date=current_date, status='completed').count()
            daily_data.append({
                'date': current_date.strftime('%d.%m'),
                'total': daily_bookings,
                'completed': daily_completed
            })
            current_date += timedelta(days=1)
        
        chart_data = {
            'labels': [item['date'] for item in daily_data],
            'datasets': [
                {
                    'label': 'Всего записей',
                    'data': [item['total'] for item in daily_data],
                    'borderColor': 'rgb(59, 130, 246)',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)'
                },
                {
                    'label': 'Завершенные',
                    'data': [item['completed'] for item in daily_data],
                    'borderColor': 'rgb(34, 197, 94)',
                    'backgroundColor': 'rgba(34, 197, 94, 0.1)'
                }
            ]
        }
        
        return Response({
            'summary': bookings_data,
            'chart_data': chart_data
        })

class AnalyticsReportListCreateAPIView(generics.ListCreateAPIView):
    """API для работы с отчетами аналитики"""
    serializer_class = AnalyticsReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.business:
            return AnalyticsReport.objects.filter(business=user.business).order_by('-created_at')
        return AnalyticsReport.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business)

class AnalyticsDashboardAPIView(APIView):
    """API для работы с настройками дашборда"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not user.business:
            return Response({'error': 'У вас нет привязанного бизнеса'}, status=400)
        
        dashboard, created = AnalyticsDashboard.objects.get_or_create(business=user.business)
        serializer = AnalyticsDashboardSerializer(dashboard)
        return Response(serializer.data)
    
    def put(self, request):
        user = request.user
        if not user.business:
            return Response({'error': 'У вас нет привязанного бизнеса'}, status=400)
        
        dashboard, created = AnalyticsDashboard.objects.get_or_create(business=user.business)
        serializer = AnalyticsDashboardSerializer(dashboard, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class ExportAnalyticsAPIView(APIView):
    """API для экспорта данных аналитики"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not user.business:
            return Response({'error': 'У вас нет привязанного бизнеса'}, status=400)
        
        report_type = request.GET.get('report_type', 'revenue')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        format_type = request.GET.get('format', 'json')
        
        if not start_date or not end_date:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics_service = AnalyticsService(user.business)
        
        if report_type == 'revenue':
            data = analytics_service.get_revenue_data(start_date, end_date)
        elif report_type == 'clients':
            data = analytics_service.get_clients_data(start_date, end_date)
        elif report_type == 'services':
            data = analytics_service.get_services_data(start_date, end_date)
        elif report_type == 'employees':
            data = analytics_service.get_employees_data(start_date, end_date)
        elif report_type == 'bookings':
            data = analytics_service.get_bookings_data(start_date, end_date)
        else:
            return Response({'error': 'Неизвестный тип отчета'}, status=400)
        
        # Сохраняем отчет
        report = AnalyticsReport.objects.create(
            business=user.business,
            report_type=report_type,
            period_type='daily',
            start_date=start_date,
            end_date=end_date,
            data=data
        )
        
        return Response({
            'report_id': report.id,
            'data': data
        }) 