from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.models import User
from .models import Service, ServiceCategory
from .serializers import ServiceSerializer, ServiceCategorySerializer, ServiceShortSerializer
from rest_framework.views import APIView
from rest_framework import status
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
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

class ServiceCategoryViewSet(AdminOrOwnerOnlyMixin, viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['business']

    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        """Получить все услуги в категории"""
        category = self.get_object()
        services = category.services.all()
        serializer = ServiceShortSerializer(services, many=True)
        return Response(serializer.data)

class ServiceViewSet(AdminOrOwnerOnlyMixin, viewsets.ModelViewSet):
    queryset = Service.objects.all().select_related('category', 'business')
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['business', 'category', 'is_active']

    def get_queryset(self):
        queryset = super().get_queryset()
        business_id = self.request.query_params.get('business', None)
        is_active = self.request.query_params.get('is_active', None)
        print(f"[DEBUG] /services/api/services/ business_id={business_id} is_active={is_active}")
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        else:
            queryset = queryset.none()
        # Убираем фильтр по is_active по умолчанию - показываем все услуги
        # if is_active is None:
        #     queryset = queryset.filter(is_active=True)
        print(f"[DEBUG] /services/api/services/ count={queryset.count()} ids={[s.id for s in queryset]}")
        return queryset

    def create(self, request, *args, **kwargs):
        print(f"[DEBUG] create: request.data={request.data}")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print(f"[DEBUG] create: validation errors={serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        print(f"[DEBUG] create: serializer is valid, creating...")
        self.perform_create(serializer)
        print(f"[DEBUG] create: service created successfully, id={serializer.instance.id}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Переопределяем update для проверки business_id"""
        try:
            instance = Service.objects.get(id=kwargs.get('pk'))
            business_id = request.data.get('business_id')
            
            print(f"[DEBUG] update: service_id={instance.id}, service_business_id={instance.business_id}, request_business_id={business_id}")
            
            # Проверяем, что услуга принадлежит правильному бизнесу
            if business_id and instance.business_id != int(business_id):
                return Response({'error': 'Услуга не найдена'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            self.perform_update(serializer)
            return Response(serializer.data)
            
        except Service.DoesNotExist:
            return Response({'error': 'Услуга не найдена'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[DEBUG] update error: {e}")
            return Response({'error': 'Ошибка обновления'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """Переопределяем destroy для проверки business_id"""
        try:
            instance = Service.objects.get(id=kwargs.get('pk'))
            business_id = request.query_params.get('business', None)
            
            print(f"[DEBUG] destroy: service_id={instance.id}, service_business_id={instance.business_id}, request_business_id={business_id}")
            
            # Проверяем, что услуга принадлежит правильному бизнесу
            if business_id and instance.business_id != int(business_id):
                return Response({'error': 'Услуга не найдена'}, status=status.HTTP_404_NOT_FOUND)
            
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Service.DoesNotExist:
            return Response({'error': 'Услуга не найдена'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[DEBUG] destroy error: {e}")
            return Response({'error': 'Ошибка удаления'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Получить услуги, сгруппированные по категориям"""
        business_id = request.query_params.get('business', None)
        queryset = self.get_queryset()
        
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        
        categories = ServiceCategory.objects.filter(
            services__in=queryset
        ).distinct().prefetch_related('services')
        
        result = []
        for category in categories:
            category_services = category.services.filter(id__in=queryset.values_list('id', flat=True))
            result.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'services': ServiceShortSerializer(category_services, many=True).data
            })
        
        return Response(result)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return response

# --- Единый API для services.html ---
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def services_page_data(request):
    """
    Возвращает структуру для services.html:
    [
      {
        id, name, description, services: [ {id, name, price, duration, ...} ]
      }, ...
    ]
    """
    business_id = request.query_params.get('business')
    if not business_id:
        return Response({'detail': 'business param required'}, status=status.HTTP_400_BAD_REQUEST)
    categories = ServiceCategory.objects.filter(business_id=business_id).order_by('name').prefetch_related('services')
    result = []
    for category in categories:
        services = category.services.all().order_by('name')
        result.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'services': ServiceSerializer(services, many=True).data
        })
    return Response(result)

services_page_data = admin_or_owner_required(services_page_data)

def services_page(request):
    lang = get_user_language(request)
    is_mob = is_mobile(request)
    template = f"services/{lang}/services_mobile.html" if is_mob else f"services/{lang}/services.html"
    return render(request, template, {"current_language": lang})

services_page = admin_or_owner_required(services_page)
