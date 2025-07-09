from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', views.NotificationPageView.as_view(), name='notification_list'),
    path('', include(router.urls)),
] 