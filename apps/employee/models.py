from django.db import models
from django.conf import settings
from apps.employees.models import Employee

# Create your models here.

class EmployeeAIAdvice(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='ai_advices', verbose_name='Сотрудник')
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    icon = models.CharField(max_length=50, verbose_name='Иконка', default='bot')
    priority = models.IntegerField(default=0, verbose_name='Приоритет')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        unique_together = ('employee', 'title')
        verbose_name = 'ИИ-совет сотрудника'
        verbose_name_plural = 'ИИ-советы сотрудников'

    def __str__(self):
        return f"{self.employee}: {self.title}"
