from django.db import models
from apps.businesses.models import Business

# Create your models here.

class ServiceCategory(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='service_categories', verbose_name='Бизнес')
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(verbose_name="Описание", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Категория услуг"
        verbose_name_plural = "Категории услуг"
        ordering = ["name"]
        unique_together = ["business", "name"]

    def __str__(self):
        return self.name

class Service(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='services', verbose_name='Бизнес')
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services', verbose_name='Категория', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name="Название услуги")
    description = models.TextField(verbose_name="Описание", blank=True)
    price = models.PositiveIntegerField(verbose_name="Стоимость (₽)", null=True, blank=True)
    duration = models.PositiveIntegerField(verbose_name="Длительность (минуты)", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ["category", "name"]
        unique_together = ["business", "category", "name"]

    def __str__(self):
        category_name = self.category.name if self.category else "Без категории"
        return f"{self.name} ({category_name})"

    @property
    def formatted_price(self):
        """Возвращает отформатированную цену"""
        if self.price:
            return f"₽ {self.price:,}".replace(',', ' ')
        return "Не указана"

    @property
    def formatted_duration(self):
        """Возвращает отформатированную длительность"""
        if not self.duration:
            return "Не указана"
        
        hours = self.duration // 60
        minutes = self.duration % 60
        
        if hours > 0:
            if minutes > 0:
                return f"{hours} ч {minutes} мин"
            else:
                return f"{hours} ч"
        else:
            return f"{minutes} мин"
