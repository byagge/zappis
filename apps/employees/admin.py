from django.contrib import admin
from .models import Employee, Position

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'business', 'position', 'phone', 'email', 'status', 'experience', 'is_master', 'photo_tag',
        'user', 'birthDate', 'education', 'skills', 'address', 'salary', 'schedule', 'clientsCount', 'rating',
        'passportNumber', 'passportIssued', 'passportExpiry', 'taxId', 'bankAccount', 'bankName',
        'emergencyContact', 'emergencyContactName', 'emergencyContactRelation', 'startDate', 'contractNumber',
        'contractExpiry', 'vacationDaysTotal', 'vacationDaysUsed', 'sickDaysTotal', 'sickDaysUsed',
        'certifications', 'languages', 'achievements', 'notes', 'equipment', 'insuranceNumber', 'insuranceExpiry',
        'is_master', 'photo'
    )
    list_filter = ('business', 'is_master', 'position', 'status')
    search_fields = (
        'name', 'position__name', 'phone', 'email', 'passportNumber', 'bankAccount', 'taxId',
        'emergencyContact', 'emergencyContactName', 'address', 'skills', 'education', 'languages', 'notes',
    )
    readonly_fields = ('photo_tag',)
    fields = (
        'user', 'business', 'name', 'position', 'phone', 'email', 'status', 'experience', 'birthDate',
        'education', 'skills', 'address', 'salary', 'schedule', 'clientsCount', 'rating', 'passportNumber',
        'passportIssued', 'passportExpiry', 'taxId', 'bankAccount', 'bankName', 'emergencyContact',
        'emergencyContactName', 'emergencyContactRelation', 'startDate', 'contractNumber', 'contractExpiry',
        'vacationDaysTotal', 'vacationDaysUsed', 'sickDaysTotal', 'sickDaysUsed', 'certifications', 'languages',
        'achievements', 'notes', 'equipment', 'insuranceNumber', 'insuranceExpiry', 'performanceReviews',
        'trainingHistory', 'workSchedule', 'salaryHistory', 'documents', 'is_master', 'photo', 'photo_tag'
    )

    def photo_tag(self, obj):
        if obj.photo:
            return f'<img src="{obj.photo.url}" style="max-height:60px;max-width:60px;border-radius:8px;" />'
        return ""
    photo_tag.short_description = 'Фото'
    photo_tag.allow_tags = True

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_subtype')
    list_filter = ('business_subtype',)
    search_fields = ('name',)
