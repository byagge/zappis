from django.db import models
from django.conf import settings
from apps.businesses.models import Business, BusinessType, BusinessSubtype
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField, EncryptedDateField, EncryptedIntegerField

class Position(models.Model):
    name = models.CharField(max_length=100, verbose_name='Должность')
    business_subtype = models.ForeignKey(BusinessSubtype, on_delete=models.CASCADE, related_name='positions', verbose_name='Субкатегория бизнеса')

    def __str__(self):
        return self.name

class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee', verbose_name='Пользователь', null=True, blank=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='employees', verbose_name='Бизнес')
    name = EncryptedCharField(max_length=255, verbose_name='Имя')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name='Должность')
    phone = EncryptedCharField(max_length=20, verbose_name='Телефон')
    email = EncryptedCharField(max_length=255, verbose_name='Email')
    status = models.CharField(max_length=20, default='active', verbose_name='Статус')
    experience = models.PositiveIntegerField(default=0, verbose_name='Опыт работы (лет)')
    birthDate = EncryptedDateField(null=True, blank=True, verbose_name='Дата рождения')
    education = EncryptedCharField(max_length=255, blank=True, verbose_name='Образование')
    skills = EncryptedTextField(blank=True, verbose_name='Навыки')
    address = EncryptedCharField(max_length=255, blank=True, verbose_name='Адрес')
    salary = EncryptedIntegerField(default=0, verbose_name='Зарплата')
    schedule = EncryptedCharField(max_length=100, blank=True, verbose_name='График')
    clientsCount = models.PositiveIntegerField(default=0, verbose_name='Клиентов')
    rating = models.FloatField(default=0, verbose_name='Рейтинг')
    passportNumber = EncryptedCharField(max_length=50, blank=True, verbose_name='Номер паспорта')
    passportIssued = EncryptedDateField(null=True, blank=True, verbose_name='Дата выдачи паспорта')
    passportExpiry = EncryptedDateField(null=True, blank=True, verbose_name='Срок действия паспорта')
    taxId = EncryptedCharField(max_length=50, blank=True, verbose_name='ИНН')
    bankAccount = EncryptedCharField(max_length=50, blank=True, verbose_name='Номер счета')
    bankName = EncryptedCharField(max_length=100, blank=True, verbose_name='Название банка')
    emergencyContact = EncryptedCharField(max_length=20, blank=True, verbose_name='Телефон экстренного контакта')
    emergencyContactName = EncryptedCharField(max_length=100, blank=True, verbose_name='Имя экстренного контакта')
    emergencyContactRelation = EncryptedCharField(max_length=100, blank=True, verbose_name='Отношение экстренного контакта')
    startDate = EncryptedDateField(null=True, blank=True, verbose_name='Дата начала работы')
    contractNumber = EncryptedCharField(max_length=100, blank=True, verbose_name='Номер контракта')
    contractExpiry = EncryptedDateField(null=True, blank=True, verbose_name='Срок действия контракта')
    vacationDaysTotal = models.PositiveIntegerField(default=28, verbose_name='Всего дней отпуска')
    vacationDaysUsed = models.PositiveIntegerField(default=0, verbose_name='Использовано дней отпуска')
    sickDaysTotal = models.PositiveIntegerField(default=30, verbose_name='Всего больничных дней')
    sickDaysUsed = models.PositiveIntegerField(default=0, verbose_name='Использовано больничных дней')
    certifications = EncryptedTextField(blank=True, verbose_name='Сертификаты')
    languages = EncryptedCharField(max_length=255, blank=True, verbose_name='Языки')
    achievements = EncryptedTextField(blank=True, verbose_name='Достижения')
    notes = EncryptedTextField(blank=True, verbose_name='Примечания')
    equipment = EncryptedTextField(blank=True, verbose_name='Оборудование')
    insuranceNumber = EncryptedCharField(max_length=100, blank=True, verbose_name='Номер страховки')
    insuranceExpiry = EncryptedDateField(null=True, blank=True, verbose_name='Срок действия страховки')
    performanceReviews = models.JSONField(default=list, blank=True, verbose_name='Оценки работы')
    trainingHistory = models.JSONField(default=list, blank=True, verbose_name='История обучения')
    workSchedule = models.JSONField(default=dict, blank=True, verbose_name='График работы')
    salaryHistory = models.JSONField(default=list, blank=True, verbose_name='История зарплат')
    documents = models.JSONField(default=list, blank=True, verbose_name='Документы')
    is_master = models.BooleanField(default=False, verbose_name="Является мастером")
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True, verbose_name='Фото')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
