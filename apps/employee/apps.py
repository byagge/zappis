from django.apps import AppConfig


class EmployeeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.employee'
    verbose_name = 'Личный кабинет сотрудника'
