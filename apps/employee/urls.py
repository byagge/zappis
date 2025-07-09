from django.urls import path
from . import views
from .views import (
    EmployeeClientListAPIView, EmployeeClientsPageView,
    EmployeeBookingListCreateAPIView, EmployeeBookingRetrieveUpdateDestroyAPIView, EmployeeSchedulesPageView,
    EmployeeNotificationsPageView, EmployeeSettingsPageView,
    EmployeeProfileAPIView
)

urlpatterns = [
    path('', views.employee_dashboard, name='employee_dashboard'),
    path('overview/', views.employee_overview, name='employee_overview'),
    path('recent-activity/', views.employee_recent_activity, name='employee_recent_activity'),
    path('top-clients/', views.employee_top_clients, name='employee_top_clients'),
    path('revenue-chart/', views.employee_revenue_chart, name='employee_revenue_chart'),
    path('ai-advice/', views.employee_ai_advice, name='employee_ai_advice'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('clients/', EmployeeClientsPageView.as_view(), name='employee_clients_page'),
    path('api/clients/', EmployeeClientListAPIView.as_view(), name='employee_clients_api'),
    path('schedules/', EmployeeSchedulesPageView.as_view(), name='employee_schedules_page'),
    path('api/schedules/', EmployeeBookingListCreateAPIView.as_view(), name='employee_schedules_api'),
    path('api/schedules/<int:pk>/', EmployeeBookingRetrieveUpdateDestroyAPIView.as_view(), name='employee_schedules_api_detail'),
    path('notifications/', EmployeeNotificationsPageView.as_view(), name='employee_notifications_page'),
    path('settings/', EmployeeSettingsPageView.as_view(), name='employee_settings_page'),
    path('api/profile/', EmployeeProfileAPIView.as_view(), name='employee_profile_api'),
] 