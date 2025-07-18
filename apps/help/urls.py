from django.urls import path
from .views import (
    HelpCenterView,
    GettingStartedRecordView,
    GettingStartedProfileView,
    NotificationsView,
    SchedulesView,
    ClientsView,
    ServicesView,
    EmployeesView,
    AnalyticsView,
    SettingsView,
    PrivacyView,
    WebView,
    TasksView,
    AiView,
    FeaturesView,
    RecordsRemindersView,
)

urlpatterns = [
    path('', HelpCenterView.as_view(), name='help_center'),
    path('getting-started/', GettingStartedRecordView.as_view(), name='getting_started_record'),
    path('getting-started-profile/', GettingStartedProfileView.as_view(), name='getting_started_profile'),
    path('notifications/', NotificationsView.as_view(), name="help-notifications"),
    path('schedules/', SchedulesView.as_view(), name="help-schedules"),
    path('clients/', ClientsView.as_view(), name="help-clients"),
    path('services/', ServicesView.as_view(), name="help-services"),
    path('employees/', EmployeesView.as_view(), name="help-employees"),
    path('analytics/', AnalyticsView.as_view(), name="help-analytics"),
    path('settings/', SettingsView.as_view(), name="help-settings"),
    path('privacy/', PrivacyView.as_view(), name="help-privacy"),
    path('web/', WebView.as_view(), name="help-web"),
    path('tasks/', TasksView.as_view(), name="help-tasks"),
    path('ai/', AiView.as_view(), name="help-ai"),
    path('features/', FeaturesView.as_view(), name="help-features"),
    path('records-reminders/', RecordsRemindersView.as_view(), name="help-records-reminders"),
]
