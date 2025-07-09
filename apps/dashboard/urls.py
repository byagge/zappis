from django.urls import path
from . import views

urlpatterns = [
    # Основные эндпоинты dashboard
    path('overview/', views.DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('revenue-chart/', views.RevenueChartView.as_view(), name='revenue-chart'),
    path('recent-activity/', views.RecentActivityView.as_view(), name='recent-activity'),
    path('ai-insights/', views.AIInsightsView.as_view(), name='ai-insights'),
    
    # Дополнительная статистика
    path('popular-services/', views.PopularServicesView.as_view(), name='popular-services'),
    path('top-clients/', views.TopClientsView.as_view(), name='top-clients'),
    
    # Детальная статистика и финансы
    path('stats/', views.BusinessStatsView.as_view(), name='business-stats'),
    path('finance/', views.FinanceRecordsView.as_view(), name='finance-records'),
    
    # HTML страница dashboard
    path('', views.DashboardTemplateView.as_view(), name='dashboard-page'),
    
    # Демо-версия dashboard
    path('demo/', views.DashboardDemoTemplateView.as_view(), name='dashboard-demo'),
    
    # API для мобильного приложения
    path('api/services/', views.AllServicesAPIView.as_view(), name='all-services'),
    path('api/clients/', views.AllClientsAPIView.as_view(), name='all-clients'),
] 