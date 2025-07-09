from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings
from apps.businesses.models import BusinessType, BusinessSubtype, Business
from apps.main.models import City
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email=email, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        EMPLOYEE = 'employee', 'Employee'
        USER = 'user', 'User'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=False, blank=True, null=True, verbose_name='Email')
    password = models.CharField(max_length=128, verbose_name='Пароль')
    full_name = models.CharField(max_length=255, verbose_name='ФИО')
    phone_number = models.CharField(
        max_length=20, blank=False, null=False, unique=True,
        validators=[RegexValidator(r'^\+?\d{9,15}$', 'Введите корректный номер телефона.')],
        verbose_name='Телефон'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='Роль'
    )
    business = models.ForeignKey(
        Business, on_delete=models.SET_NULL, blank=True, null=True, related_name='users', verbose_name='Бизнес'
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    is_phone_verified = models.BooleanField(default=False, verbose_name='Телефон подтвержден')
    preferred_language = models.CharField(max_length=10, default='ru', verbose_name='Язык')
    user_timezone = models.CharField(max_length=50, default='Asia/Bishkek', verbose_name='Часовой пояс')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Дата регистрации')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_staff = models.BooleanField(default=False, verbose_name='Сотрудник')
    is_superuser = models.BooleanField(default=False, verbose_name='Суперпользователь')
    last_login_time = models.DateTimeField(blank=True, null=True, verbose_name='Время последнего входа')
    last_login_ip = models.CharField(max_length=45, blank=True, null=True, verbose_name='IP адрес последнего входа')
    last_login_device = models.CharField(max_length=255, blank=True, null=True, verbose_name='Устройство входа')
    last_login_device_time = models.DateTimeField(blank=True, null=True, verbose_name='Время входа с устройства')
    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Город'
    )
    country = models.CharField(max_length=50, default='Кыргызстан', verbose_name='Страна')
    groups = models.ManyToManyField(
        Group,
        related_name='accounts_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='accounts_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    is_trial = models.BooleanField(default=True, verbose_name='Пробный период активен')
    is_tarifed = models.BooleanField(default=True, verbose_name='Тариф активен')
    is_dashboard_welcome_showed = models.BooleanField(default=False, verbose_name='Показан welcome-заглушка Dashboard')

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email or self.phone_number or str(self.id)

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Персональная информация', {'fields': ('full_name', 'email', 'avatar', 'role', 'business', 'city', 'country', 'preferred_language', 'user_timezone')}),
    )

    @property
    def is_trial_active(self):
        if not self.is_trial:
            return False
        if self.date_joined:
            trial_days = 30
            return (timezone.now() - self.date_joined).days < trial_days
        return False

    def save(self, *args, **kwargs):
        if self.is_trial and self.date_joined:
            trial_days = 30
            if (timezone.now() - self.date_joined).days >= trial_days:
                self.is_trial = False
                self.is_tarifed = False
        super().save(*args, **kwargs)

# Модель для хранения сессии регистрации
class RegistrationSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    agree_to_terms = models.BooleanField()
    company_name = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.ForeignKey(BusinessType, on_delete=models.SET_NULL, blank=True, null=True)
    business_subtype = models.ForeignKey(BusinessSubtype, on_delete=models.SET_NULL, blank=True, null=True)
    employees_count = models.CharField(max_length=10, blank=True, null=True)
    sphere = models.CharField(max_length=100, blank=True, null=True)
    company_type = models.CharField(max_length=100, blank=True, null=True)
    specialists_count = models.CharField(max_length=10, blank=True, null=True)
    code = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def check_code(self, code):
        return self.code == code
