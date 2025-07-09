from django.contrib import admin
from .models import AnalyticsReport, AnalyticsDashboard, AnalyticsMetric

@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ['business', 'report_type', 'period_type', 'start_date', 'end_date', 'created_at']
    list_filter = ['report_type', 'period_type', 'created_at']
    search_fields = ['business__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

@admin.register(AnalyticsDashboard)
class AnalyticsDashboardAdmin(admin.ModelAdmin):
    list_display = ['business', 'created_at', 'updated_at']
    search_fields = ['business__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AnalyticsMetric)
class AnalyticsMetricAdmin(admin.ModelAdmin):
    list_display = ['business', 'metric_type', 'value', 'date', 'period']
    list_filter = ['metric_type', 'period', 'date']
    search_fields = ['business__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'date' 