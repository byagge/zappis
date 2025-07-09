from django.db import models
from django.core.exceptions import ValidationError
from apps.employees.models import Employee
from apps.services.models import Service
from apps.clients.models import Client

class Booking(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент", related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Услуга")
    master = models.ForeignKey(Employee, on_delete=models.PROTECT, limit_choices_to={"is_master": True}, verbose_name="Мастер")
    date = models.DateField(verbose_name="Дата записи")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    price = models.PositiveIntegerField(verbose_name="Стоимость (₽)", help_text="Фактическая стоимость услуги")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ["-date", "-start_time"]
        indexes = [
            models.Index(fields=["date", "master"]),
        ]
        unique_together = ("master", "date", "start_time")

    def clean(self):
        super().clean()
        
        # Проверяем, что время окончания больше времени начала
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Время окончания должно быть позже времени начала")
        
        # Проверяем конфликты времени для того же мастера в тот же день
        if self.master and self.date and self.start_time and self.end_time:
            conflicting_bookings = Booking.objects.filter(
                master=self.master,
                date=self.date
            ).exclude(pk=self.pk)  # Исключаем текущую запись при редактировании
            
            for booking in conflicting_bookings:
                # Проверяем пересечение интервалов
                if (self.start_time < booking.end_time and self.end_time > booking.start_time):
                    raise ValidationError(
                        f"Мастер {self.master} уже занят в это время. "
                        f"Существующая запись: {booking.start_time} - {booking.end_time}"
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client} — {self.service} ({self.date} {self.start_time})"
