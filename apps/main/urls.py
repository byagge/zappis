from django.urls import path
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.main_page, name='main'),
    path('partners/', TemplateView.as_view(template_name='partners.html'), name='landing'),
    path('api/cities/', views.city_list, name='city-list'),
    path('api/business/<int:business_id>/photos/', views.business_photos_api, name='business-photos-api'),
    path('services/', RedirectView.as_view(url='/api/services/', permanent=False), name='services-redirect'),
    path('api/save-city/', views.save_city, name='save-city'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('technologies/', TemplateView.as_view(template_name='technologies.html'), name='technologies'),
    path('cookies/', TemplateView.as_view(template_name='cookies.html'), name='cookies'),
    path('export/', TemplateView.as_view(template_name='export.html'), name='export'),
    path('send_demo/', views.send_demo, name='send_demo'),
    
    # Demo Dashboard URLs - автоматическое определение устройства
    path('demo/', views.DemoDashboardView.as_view(), name='demo_dashboard'),
    path('demo/ky/', views.DemoDashboardView.as_view(), name='demo_dashboard_ky'),
    
    # Старые URL для прямого доступа к конкретным версиям (для тестирования)
    path('demo/desktop/', TemplateView.as_view(template_name='ru/demo_dashboard.html'), name='demo_dashboard_desktop'),
    path('demo/mobile/', TemplateView.as_view(template_name='ru/demo_dashboard_mobile.html'), name='demo_dashboard_mobile'),
    path('demo/ky/desktop/', TemplateView.as_view(template_name='ky/demo_dashboard.html'), name='demo_dashboard_ky_desktop'),
    path('demo/ky/mobile/', TemplateView.as_view(template_name='ky/demo_dashboard_mobile.html'), name='demo_dashboard_mobile_ky'),
    
    # Тестовая страница для определения устройства
    path('device-test/', TemplateView.as_view(template_name='device_test.html'), name='device_test'),
    
    # Тестовая страница 404 (для разработки)
    path('test-404/', views.custom_404, name='test_404'),
]
