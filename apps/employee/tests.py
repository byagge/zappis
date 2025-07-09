from django.test import TestCase
from django.contrib.auth import get_user_model
from employees.models import Employee
from .models import EmployeeDashboard, EmployeeSchedule, EmployeeNotification, EmployeeClient
from datetime import datetime, timedelta

# Create your tests here.

class EmployeeModelsTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create(username='testuser')
        self.employee = Employee.objects.create(user=user)

    def test_dashboard_create(self):
        dashboard = EmployeeDashboard.objects.create(employee=self.employee, notes='Test')
        self.assertEqual(dashboard.notes, 'Test')

    def test_schedule_create(self):
        schedule = EmployeeSchedule.objects.create(
            employee=self.employee,
            title='Meeting',
            start=datetime.now(),
            end=datetime.now() + timedelta(hours=1),
            description='Test desc'
        )
        self.assertEqual(schedule.title, 'Meeting')

    def test_notification_create(self):
        notification = EmployeeNotification.objects.create(employee=self.employee, message='Hello')
        self.assertFalse(notification.is_read)

    def test_client_create(self):
        client = EmployeeClient.objects.create(employee=self.employee, name='Client')
        self.assertEqual(client.name, 'Client')
