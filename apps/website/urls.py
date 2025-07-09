from django.urls import path
from . import views

urlpatterns = [
    path('<str:username>/', views.public_website, name='public_website'),
    path('api/website/<str:username>/', views.get_website_data, name='get_website_data'),
    path('api/website/<str:username>/services/', views.get_services, name='get_services'),
    path('api/website/<str:username>/employees/', views.get_employees, name='get_employees'),
    path('api/website/<str:username>/schedule/', views.get_schedule, name='get_schedule'),
    path('api/website/<str:username>/view/', views.increment_views, name='increment_views'),
    path('api/website/<str:username>/booking/', views.create_booking, name='create_booking'),
    path('api/website/<str:username>/test-booking/', views.create_test_booking, name='create_test_booking'),
] 