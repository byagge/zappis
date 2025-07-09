from rest_framework.routers import DefaultRouter
from django.urls import path, include
from django.shortcuts import render
from .views import ServiceViewSet, ServiceCategoryViewSet, services_page_data, services_page

router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'categories', ServiceCategoryViewSet, basename='servicecategory')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/page_data/', services_page_data, name='services-page-data'),
    
    # Template view
    path('', services_page, name='services_page'),
]