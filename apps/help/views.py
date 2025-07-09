from django.shortcuts import render
from django.http import HttpRequest
from django.views.generic import TemplateView

def detect_language(request: HttpRequest) -> str:
    """
    Приоритет: GET параметр lang -> авторизованный пользователь -> Accept-Language header -> по умолчанию 'ru'
    """
    lang = request.GET.get('lang', '').lower()
    if lang in ['ru', 'ky']:
        return lang
    user = getattr(request, 'user', None)
    if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
        lang = getattr(user, 'preferred_language', None)
        if lang in ['ru', 'ky']:
            return lang
    # Проверяем Accept-Language header
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    if 'ky' in accept_language.lower():
        return 'ky'
    elif 'ru' in accept_language.lower():
        return 'ru'
    
    # По умолчанию русский
    return 'ru'

class HelpCenterView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/help.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class GettingStartedRecordView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/getting_started_record.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class GettingStartedProfileView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/getting_started_profile.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class NotificationsView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/notifications.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class SchedulesView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/schedules.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class ClientsView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/clients.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class ServicesView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/services.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class EmployeesView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/help-employees.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class AnalyticsView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/analytics.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class SettingsView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/settings.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class PrivacyView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/privacy.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class WebView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/web.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class TasksView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/tasks.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class AiView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/ai.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class FeaturesView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/features.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context

class RecordsRemindersView(TemplateView):
    def get_template_names(self):
        lang = detect_language(self.request)
        return [f'{lang}/records_reminders.html']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lang'] = detect_language(self.request)
        return context
