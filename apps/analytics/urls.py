from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Страница аналитики
    path('', views.AnalyticsPageView.as_view(), name='analytics_page'),
    
    # API для дашборда
    path('api/dashboard/summary/', views.DashboardSummaryAPIView.as_view(), name='dashboard_summary'),
    path('api/dashboard/settings/', views.AnalyticsDashboardAPIView.as_view(), name='dashboard_settings'),
    
    # API для данных
    path('api/data/revenue/', views.RevenueDataAPIView.as_view(), name='revenue_data'),
    path('api/data/clients/', views.ClientsDataAPIView.as_view(), name='clients_data'),
    path('api/data/services/', views.ServicesDataAPIView.as_view(), name='services_data'),
    path('api/data/employees/', views.EmployeesDataAPIView.as_view(), name='employees_data'),
    path('api/data/bookings/', views.BookingsDataAPIView.as_view(), name='bookings_data'),
    
    # API для отчетов
    path('api/reports/', views.AnalyticsReportListCreateAPIView.as_view(), name='reports_list'),
    path('api/export/', views.ExportAnalyticsAPIView.as_view(), name='export_analytics'),
] 