from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.businesses.models import Business
from apps.analytics.models import AnalyticsReport, AnalyticsDashboard, AnalyticsMetric, AnalyticsService
from datetime import date, timedelta

User = get_user_model()

class AnalyticsModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.business = Business.objects.create(
            name='Test Business',
            owner=self.user
        )
        self.user.business = self.business
        self.user.save()

    def test_analytics_report_creation(self):
        report = AnalyticsReport.objects.create(
            business=self.business,
            report_type='revenue',
            period_type='monthly',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            data={'test': 'data'}
        )
        self.assertEqual(report.business, self.business)
        self.assertEqual(report.report_type, 'revenue')
        self.assertEqual(str(report), f"Выручка - {report.start_date} - {report.end_date}")

    def test_analytics_dashboard_creation(self):
        dashboard = AnalyticsDashboard.objects.create(
            business=self.business,
            widgets=['revenue_chart', 'clients_chart'],
            layout={'columns': 2},
            settings={'theme': 'light'}
        )
        self.assertEqual(dashboard.business, self.business)
        self.assertEqual(len(dashboard.widgets), 2)

    def test_analytics_metric_creation(self):
        metric = AnalyticsMetric.objects.create(
            business=self.business,
            metric_type='revenue',
            value=1000.00,
            date=date.today(),
            period='daily'
        )
        self.assertEqual(metric.business, self.business)
        self.assertEqual(metric.value, 1000.00)

class AnalyticsServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.business = Business.objects.create(
            name='Test Business',
            owner=self.user
        )
        self.user.business = self.business
        self.user.save()
        self.analytics_service = AnalyticsService(self.business)

    def test_calculate_percentage_change(self):
        # Тест расчета процентного изменения
        change = self.analytics_service._calculate_percentage_change(100, 120)
        self.assertEqual(change, 20.0)
        
        change = self.analytics_service._calculate_percentage_change(100, 80)
        self.assertEqual(change, -20.0)
        
        change = self.analytics_service._calculate_percentage_change(0, 50)
        self.assertEqual(change, 100.0)

    def test_calculate_growth_rate(self):
        # Тест расчета темпа роста
        from django.db.models import QuerySet
        from unittest.mock import Mock
        
        mock_queryset = Mock(spec=QuerySet)
        mock_queryset.count.return_value = 10
        
        rate = self.analytics_service._calculate_growth_rate(
            mock_queryset, 
            date.today(), 
            date.today() + timedelta(days=10)
        )
        self.assertEqual(rate, 1.0)  # 10 клиентов за 10 дней = 1 в день 