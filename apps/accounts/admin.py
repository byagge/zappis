from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('id', 'phone_number', 'password'), 'description': 'Основная информация для входа.'}),
        ('Персональная информация', {'fields': ('full_name', 'email', 'avatar', 'role', 'business', 'city', 'country', 'preferred_language', 'user_timezone', 'is_trial', 'is_tarifed', 'is_trial_active', 'is_dashboard_welcome_showed'), 'description': 'Профиль пользователя.'}),
        ('Безопасность', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_phone_verified', 'groups', 'user_permissions'), 'description': 'Права и статусы.'}),
        ('Входы', {'fields': ('last_login_time', 'last_login_ip', 'last_login_device', 'last_login_device_time', 'date_joined'), 'description': 'История входов.'}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number', 'full_name', 'email', 'avatar', 'role', 'business',
                'city', 'country', 'preferred_language', 'user_timezone',
                'is_trial', 'is_tarifed',
                'is_active', 'is_staff', 'is_superuser', 'is_phone_verified',
                'groups', 'user_permissions',
                'password1', 'password2',
            ),
            'description': 'Создание нового пользователя.'
        }),
    )
    list_display = ('id', 'phone_number', 'full_name', 'email', 'role', 'business', 'city', 'country', 'is_trial', 'is_tarifed', 'is_trial_active', 'is_active', 'is_staff', 'is_superuser', 'is_phone_verified', 'last_login_time', 'last_login_ip')
    list_filter = ('role', 'business', 'city', 'country', 'is_trial', 'is_tarifed', 'is_active', 'is_staff', 'is_superuser', 'is_phone_verified')
    search_fields = ('id', 'phone_number', 'full_name', 'email', 'country')
    ordering = ('-date_joined',)
    readonly_fields = ('id', 'last_login_time', 'last_login_ip', 'last_login_device', 'last_login_device_time', 'date_joined', 'is_trial_active')
