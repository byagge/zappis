from rest_framework import serializers
from .models import Employee, Position
from apps.businesses.models import BusinessType, BusinessSubtype

class EmployeeSerializer(serializers.ModelSerializer):
    """
    Основной сериализатор для модели Employee
    """
    position = serializers.CharField(source='position.name', read_only=True)
    position_id = serializers.IntegerField(source='position.id', read_only=True)
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class EmployeeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания сотрудника
    """
    class Meta:
        model = Employee
        fields = [
            'name', 'position', 'phone', 'email', 'status', 'experience',
            'birthDate', 'education', 'skills', 'address', 'salary', 'schedule',
            'clientsCount', 'rating', 'passportNumber', 'passportIssued', 'passportExpiry',
            'taxId', 'bankAccount', 'bankName', 'emergencyContact', 'emergencyContactName',
            'emergencyContactRelation', 'startDate', 'contractNumber', 'contractExpiry',
            'vacationDaysTotal', 'vacationDaysUsed', 'sickDaysTotal', 'sickDaysUsed',
            'certifications', 'languages', 'achievements', 'notes', 'equipment',
            'insuranceNumber', 'insuranceExpiry', 'performanceReviews', 'trainingHistory',
            'workSchedule', 'salaryHistory', 'documents', 'is_master'
        ]
        # Поля business и user устанавливаются автоматически в perform_create

class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления сотрудника
    """
    class Meta:
        model = Employee
        fields = [
            'name', 'position', 'phone', 'email', 'status', 'experience',
            'birthDate', 'education', 'skills', 'address', 'salary', 'schedule',
            'clientsCount', 'rating', 'passportNumber', 'passportIssued', 'passportExpiry',
            'taxId', 'bankAccount', 'bankName', 'emergencyContact', 'emergencyContactName',
            'emergencyContactRelation', 'startDate', 'contractNumber', 'contractExpiry',
            'vacationDaysTotal', 'vacationDaysUsed', 'sickDaysTotal', 'sickDaysUsed',
            'certifications', 'languages', 'achievements', 'notes', 'equipment',
            'insuranceNumber', 'insuranceExpiry', 'performanceReviews', 'trainingHistory',
            'workSchedule', 'salaryHistory', 'documents', 'is_master'
        ]

class EmployeeListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка сотрудников (сокращенная информация)
    """
    class Meta:
        model = Employee
        fields = [
            'id', 'name', 'position', 'phone', 'email', 'status', 'experience',
            'clientsCount', 'rating', 'salary'
        ]

class EmployeeStatisticsSerializer(serializers.Serializer):
    """
    Сериализатор для статистики сотрудников
    """
    total_employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    vacation_employees = serializers.IntegerField()
    sick_employees = serializers.IntegerField()
    position_stats = serializers.ListField()
    avg_rating = serializers.FloatField()
    total_clients = serializers.IntegerField()

class PositionSerializer(serializers.ModelSerializer):
    business_subtype = serializers.StringRelatedField()
    class Meta:
        model = Position
        fields = ['id', 'name', 'business_subtype']

class BusinessTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessType
        fields = ['id', 'name']

class BusinessSubtypeSerializer(serializers.ModelSerializer):
    business_type = serializers.StringRelatedField()
    class Meta:
        model = BusinessSubtype
        fields = ['id', 'name', 'business_type'] 

class EmployeeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'is_master'] 