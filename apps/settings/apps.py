from django.apps import AppConfig

class SettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.settings'
 
    def ready(self):
        import apps.settings.signals 