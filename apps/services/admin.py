from django.contrib import admin
from .models import Service, ServiceCategory

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'description', 'created_at')
    list_filter = ('business', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('business', 'name')
    fields = ('business', 'name', 'description')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'business', 'formatted_price', 'formatted_duration', 'is_active', 'created_at')
    list_filter = ('business', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    ordering = ('business', 'category', 'name')
    fields = ('business', 'category', 'name', 'description', 'price', 'duration', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    
    def formatted_price(self, obj):
        return obj.formatted_price
    formatted_price.short_description = 'Стоимость'
    
    def formatted_duration(self, obj):
        return obj.formatted_duration
    formatted_duration.short_description = 'Длительность'
