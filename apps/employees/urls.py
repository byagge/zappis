from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from . import views

# Создаем роутер для ViewSet
router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='employee')

urlpatterns = [
    # Главная страница сотрудников (список)
    path('', views.employees_page, name='employees-page'),
    # Профиль сотрудника (адаптивно)
    path('profile/', views.edata_page, name='edata-page'),
    # DRF ViewSet URLs (если нужно)
    path('api/', include(router.urls)),
    # Совместимость с фронтендом (REST API)
    path('api/employees/', views.employee_list_api, name='employee_list_api'),
    path('api/employees/<int:employee_id>/', views.employee_detail_api, name='employee_detail_api'),
    path('api/positions-for-current-business/', views.positions_for_current_business, name='positions_for_current_business'),
    path('api/masters/', views.get_masters_api, name='get_masters_api'),
] 