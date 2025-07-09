from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.decorators import action
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from apps.accounts.models import User
from apps.employees.views import get_user_language, is_mobile

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

class NotificationListCreateView(AdminOrOwnerOnlyMixin, generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class NotificationDetailView(AdminOrOwnerOnlyMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class MarkAsReadView(AdminOrOwnerOnlyMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

class ToggleImportantView(AdminOrOwnerOnlyMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_important = not notification.is_important
        notification.save()
        return Response({'status': 'toggled important', 'is_important': notification.is_important})

class NotificationPageView(AdminOrOwnerOnlyMixin, TemplateView):
    def get_template_names(self):
        lang = get_user_language(self.request)
        is_mob = is_mobile(self.request)
        if is_mob:
            return [f'notifications/{lang}/notifications_mobile.html']
        return [f'notifications/{lang}/notifications.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['notifications'] = Notification.objects.filter(user=self.request.user).order_by('-date')
        context['current_language'] = get_user_language(self.request)
        return context

class NotificationViewSet(AdminOrOwnerOnlyMixin, viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        queryset = self.get_queryset().filter(is_read=False)
        queryset.update(is_read=True)
        return Response(status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def toggle_important(self, request, pk=None):
        notification = self.get_object()
        notification.is_important = not notification.is_important
        notification.save()
        return Response({'is_important': notification.is_important})
