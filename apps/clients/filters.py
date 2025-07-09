import django_filters
from .models import Client
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

class ClientFilter(django_filters.FilterSet):
    activity_status = django_filters.CharFilter(method='filter_activity_status')

    class Meta:
        model = Client
        fields = ['business', 'status', 'activity_status']

    def filter_activity_status(self, queryset, name, value):
        today = timezone.now().date()
        if value == 'active':
            # Клиенты с визитами за последние 30 дней
            return queryset.filter(bookings__date__gte=today - timedelta(days=30)).distinct()
        elif value == 'recent':
            # Клиенты с визитами за последние 90 дней, но не за последние 30
            return queryset.filter(
                bookings__date__gte=today - timedelta(days=90),
                bookings__date__lt=today - timedelta(days=30)
            ).distinct()
        elif value == 'new':
            # Клиенты, созданные менее 30 дней назад и без визитов
            return queryset.filter(
                created_at__gte=today - timedelta(days=30),
                bookings__isnull=True
            ).distinct()
        elif value == 'inactive':
            # Нет визитов за последние 90 дней
            return queryset.exclude(
                bookings__date__gte=today - timedelta(days=90)
            ).distinct()
        elif value == 'vip':
            # VIP клиенты
            return queryset.filter(status='vip')
        return queryset 