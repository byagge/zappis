from django.db import models
from apps.businesses.models import Business

class Website(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='website')
    url = models.CharField(max_length=100, unique=True, verbose_name="URL сайта")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")
    bookings_count = models.PositiveIntegerField(default=0, verbose_name="Общее количество бронирований")
    website_bookings_count = models.PositiveIntegerField(default=0, verbose_name="Бронирования через сайт")

    class Meta:
        verbose_name = "Сайт бизнеса"
        verbose_name_plural = "Сайты бизнесов"

    def save(self, *args, **kwargs):
        # url всегда равен username бизнеса
        if self.business and self.business.username:
            self.url = self.business.username
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Сайт {self.business.name} ({self.url})"

class WebsiteBooking(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='bookings')
    customer_name = models.CharField(max_length=100, verbose_name="Имя клиента")
    customer_phone = models.CharField(max_length=20, verbose_name="Телефон клиента")
    customer_email = models.EmailField(blank=True, null=True, verbose_name="Email клиента")
    service = models.CharField(max_length=200, verbose_name="Услуга")
    specialist = models.CharField(max_length=100, blank=True, null=True, verbose_name="Специалист")
    date = models.CharField(max_length=50, verbose_name="Дата")
    time = models.CharField(max_length=20, verbose_name="Время")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Бронирование с сайта"
        verbose_name_plural = "Бронирования с сайта"

    def __str__(self):
        return f"{self.customer_name} - {self.service} ({self.date})"
