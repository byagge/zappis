from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import random
import string
from apps.main.models import City
from django.db.models import Case, When, IntegerField

class BusinessType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class BusinessSubtype(models.Model):
    business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE, related_name='subtypes')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='fas fa-store', help_text='FontAwesome icon class')

    def __str__(self):
        return f"{self.business_type.name} - {self.name}"

class Business(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.ForeignKey(BusinessType, on_delete=models.SET_NULL, null=True, blank=True)
    subtype = models.ForeignKey(BusinessSubtype, on_delete=models.SET_NULL, null=True, blank=True)
    employees_count = models.CharField(
        max_length=10,
        choices=[('1-5', 'До 5'), ('5+', 'Больше 5')],
        default='1-5'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_businesses'
    )

    address = models.CharField(max_length=255, blank=True)
    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, blank=True, null=True
    )
    country = models.CharField(max_length=100, default="Kyrgyzstan")

    phone = models.CharField(max_length=20, blank=True)
    phone_contact = models.CharField(max_length=20, blank=True, verbose_name='Телефон для клиентов')
    email = models.EmailField(blank=True)
    website_url = models.URLField(blank=True)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, verbose_name='Instagram')

    timezone = models.CharField(max_length=100, default='Asia/Bishkek')
    language = models.CharField(max_length=10, default='ru')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    username = models.CharField(max_length=150, unique=True)
    referral_code = models.CharField(max_length=6, unique=True, blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_unique_referral_code()
        super().save(*args, **kwargs)

    def _generate_unique_referral_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Business.objects.filter(referral_code=code).exists():
                return code

class BusinessPhoto(models.Model):
    business = models.ForeignKey('Business', on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='business_photos/')
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Photo for {self.business.name}"

class BusinessWorkingHour(models.Model):
    DAYS = [
        ('monday', 'Понедельник'),
        ('tuesday', 'Вторник'),
        ('wednesday', 'Среда'),
        ('thursday', 'Четверг'),
        ('friday', 'Пятница'),
        ('saturday', 'Суббота'),
        ('sunday', 'Воскресенье'),
    ]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='working_hours')
    day = models.CharField(max_length=10, choices=DAYS)
    start = models.TimeField()
    end = models.TimeField()
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('business', 'day')

    def __str__(self):
        return f"{self.business.name}: {self.get_day_display()} {self.start}-{self.end} ({'вкл' if self.enabled else 'выкл'})"

    @staticmethod
    def get_week_ordering():
        return Case(
            When(day='monday', then=0),
            When(day='tuesday', then=1),
            When(day='wednesday', then=2),
            When(day='thursday', then=3),
            When(day='friday', then=4),
            When(day='saturday', then=5),
            When(day='sunday', then=6),
            output_field=IntegerField()
        )
