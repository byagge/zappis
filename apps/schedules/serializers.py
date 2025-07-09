from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Booking
from apps.employees.models import Employee
from apps.services.models import Service
from apps.clients.models import Client
from apps.clients.serializers import ClientSerializer

class EmployeeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'is_master']

class ServiceShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price']

class BookingSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all(), source='client', write_only=True, required=False)
    client_name = serializers.CharField(write_only=True, required=False)
    client_phone = serializers.CharField(write_only=True, required=False)
    client_email = serializers.EmailField(write_only=True, required=False, allow_null=True, allow_blank=True)
    master = EmployeeShortSerializer(read_only=True)
    master_id = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.filter(is_master=True), source='master', write_only=True)
    service = ServiceShortSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), source='service', write_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'client', 'client_id', 'client_name', 'client_phone', 'client_email',
            'service', 'service_id', 'master', 'master_id',
            'date', 'start_time', 'end_time', 'price', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        # Проверяем, что время окончания больше времени начала
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("Время окончания должно быть позже времени начала")
        
        # Проверяем конфликты времени
        if data.get('master') and data.get('date') and data.get('start_time') and data.get('end_time'):
            conflicting_bookings = Booking.objects.filter(
                master=data['master'],
                date=data['date']
            )
            
            # При обновлении исключаем текущую запись
            if self.instance:
                conflicting_bookings = conflicting_bookings.exclude(pk=self.instance.pk)
            
            for booking in conflicting_bookings:
                if (data['start_time'] < booking.end_time and data['end_time'] > booking.start_time):
                    raise serializers.ValidationError(
                        f"Мастер {data['master'].name} уже занят в это время. "
                        f"Существующая запись: {booking.start_time} - {booking.end_time}"
                    )
        
        return data

    def create(self, validated_data):
        client = validated_data.pop('client', None)
        client_id = None
        if client:
            client_id = client.id
        else:
            name = validated_data.pop('client_name', None)
            phone = validated_data.pop('client_phone', None)
            email = validated_data.pop('client_email', None)
            if name and phone:
                # Получаем бизнес пользователя
                user_business = self.context['request'].user.business
                if not user_business:
                    raise serializers.ValidationError('У пользователя нет привязанного бизнеса')
                
                client, created = Client.objects.get_or_create(
                    phone=phone, 
                    defaults={
                        'name': name, 
                        'email': email,
                        'business': user_business
                    }
                )
                client_id = client.id
            else:
                raise serializers.ValidationError('Необходимо указать имя и телефон клиента')
        validated_data['client_id'] = client_id
        validated_data['client'] = Client.objects.get(id=client_id)
        
        # Создаем запись
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Обрабатываем клиента при обновлении
        client = validated_data.pop('client', None)
        client_id = validated_data.pop('client_id', None)
        
        if client:
            instance.client = client
        elif client_id:
            instance.client = client_id
        else:
            # Если переданы данные клиента, создаем или обновляем клиента
            name = validated_data.pop('client_name', None)
            phone = validated_data.pop('client_phone', None)
            email = validated_data.pop('client_email', None)
            if name and phone:
                # Получаем бизнес пользователя
                user_business = self.context['request'].user.business
                if not user_business:
                    raise serializers.ValidationError('У пользователя нет привязанного бизнеса')
                
                client, created = Client.objects.get_or_create(
                    phone=phone, 
                    defaults={
                        'name': name, 
                        'email': email,
                        'business': user_business
                    }
                )
                # Если клиент уже существовал, обновляем его данные
                if not created:
                    client.name = name
                    if email:
                        client.email = email
                    client.save()
                instance.client = client
        
        # Обновляем запись
        return super().update(instance, validated_data) 