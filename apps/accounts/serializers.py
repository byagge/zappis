from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from apps.main.models import City
from apps.businesses.models import BusinessType, BusinessSubtype
from django.utils.translation import gettext_lazy as _
from .utils import send_sms
from .models import RegistrationSession
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source='city.name', read_only=True)
    class Meta:
        model = User
        fields = ('id', 'email', 'city')

class Step1Serializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(
        validators=[RegexValidator(r'^\d{9}$', 'Неверный формат телефона')]
    )
    country = serializers.CharField(default='Кыргызстан')
    city = serializers.IntegerField()
    agree_to_terms = serializers.BooleanField()

class Step2Serializer(serializers.Serializer):
    registration_id = serializers.UUIDField()
    company_name = serializers.CharField(max_length=255)
    business_type = serializers.PrimaryKeyRelatedField(queryset=BusinessType.objects.all())
    business_subtype = serializers.PrimaryKeyRelatedField(queryset=BusinessSubtype.objects.all())
    employees_count = serializers.ChoiceField(choices=[('1-5','До 5'),('5+','Больше 5')])

class Step3Serializer(serializers.Serializer):
    registration_id = serializers.UUIDField()
    code = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True, min_length=6, max_length=128)

class VerifyCodeSerializer(serializers.Serializer):
    registration_id = serializers.UUIDField()
    code = serializers.CharField(max_length=6)

from django.contrib.auth import authenticate
from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password     = serializers.CharField(write_only=True)

    def validate(self, data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        phone = data.get('phone_number')
        password = data.get('password')
        # --- Нормализация номера ---
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('996996'):
            digits = digits[3:]  # убираем лишний 996
        if digits.startswith('996'):
            phone_norm = '+996' + digits[3:]
        else:
            phone_norm = '+996' + digits
        phone = phone_norm
        user = authenticate(
            username=phone,
            password=password
        )
        if not user:
            raise serializers.ValidationError("Неверный номер телефона или пароль")
        if not user.is_active:
            raise serializers.ValidationError("Учетная запись неактивна")
        data['user'] = user
        return data

class UserSignUpSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'password', 'confirm_password')

    def validate_phone_number(self, value):
        """
        Normalize the phone number by removing all non-digit characters
        and ensuring it starts with the country code +996.
        """
        digits = re.sub(r'\D', '', value)

        if digits.startswith('0'):
            digits = digits[1:]
        
        if digits.startswith('996'):
            if len(digits) > 9: # It has country code
                digits = digits[3:]

        if len(digits) != 9:
            raise serializers.ValidationError("Номер должен состоять из 9 цифр.")

        phone_norm = f"+996{digits}"

        if User.objects.filter(phone_number=phone_norm).exists():
            raise serializers.ValidationError("Пользователь с таким номером телефона уже существует.")
        
        return phone_norm

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        validated_data.pop('confirm_password')

        user = User.objects.create_user(
            full_name=f"{first_name} {last_name}",
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            role=User.Role.USER
        )
        return user

class UserLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('preferred_language',)
