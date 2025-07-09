from django.apps import AppConfig


class BusinessesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.businesses'

    def ready(self):
        import apps.businesses.signals
