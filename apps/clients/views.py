from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.views.generic import TemplateView
from .models import Client
from .serializers import ClientSerializer
from .filters import ClientFilter
from django.http import HttpResponse
from .exporters import export_clients
import urllib.parse
from django.utils import timezone
from datetime import datetime
from rest_framework.views import APIView
from apps.employees.views import get_user_language, is_mobile

# Create your views here.

class ClientPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class ClientListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ClientPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ClientFilter
    search_fields = ['name', 'phone', 'email']

    def get_queryset(self):
        user = self.request.user
        queryset = Client.objects.all().order_by('-created_at')
        
        # Фильтруем по бизнесу пользователя
        if user.business:
            queryset = queryset.filter(business=user.business)
        else:
            # Если у пользователя нет бизнеса, возвращаем пустой queryset
            queryset = Client.objects.none()
        
        # Оптимизируем запросы с prefetch_related для связанных записей
        queryset = queryset.prefetch_related('bookings')
        
        return queryset

    def perform_create(self, serializer):
        # Автоматически устанавливаем бизнес пользователя
        serializer.save(business=self.request.user.business)

class ClientRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Client.objects.all()
        
        # Фильтруем по бизнесу пользователя
        if user.business:
            queryset = queryset.filter(business=user.business)
        else:
            queryset = Client.objects.none()
        
        # Оптимизируем запросы с prefetch_related для связанных записей
        queryset = queryset.prefetch_related('bookings')
        
        return queryset

class ClientsPageView(TemplateView):
    template_name = 'clients/clients.html'

class ClientExportAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Client.objects.all()
        if user.business:
            qs = qs.filter(business=user.business)
        else:
            return HttpResponse('Нет бизнеса', status=400)
        # Фильтры
        status = request.GET.get('status')
        activity_status = request.GET.get('activity_status')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        if status and status != 'all':
            qs = qs.filter(status=status)
        if activity_status:
            qs = ClientFilter({'activity_status': activity_status}, queryset=qs).qs
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        export_format = request.GET.get('format', 'json')
        data, content_type = export_clients(qs, export_format)
        filename = f'clients_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
        resp = HttpResponse(data, content_type=content_type)
        resp['Content-Disposition'] = f'attachment; filename*=UTF-8''{urllib.parse.quote(filename)}'
        return resp

def clients_page(request):
    lang = get_user_language(request)
    is_mob = is_mobile(request)
    template = f"clients/{lang}/@clients.html" if is_mob else f"clients/{lang}/clients.html"
    return render(request, template, {"current_language": lang})
