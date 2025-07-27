#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from apps.businesses.models import BusinessType, BusinessSubtype

def create_business_types():
    """Создает типы бизнеса для регистрации"""
    
    # Создаем основные типы бизнеса
    types_data = [
        {
            'name': 'Салон красоты',
            'subtypes': ['Парикмахерская', 'Маникюр', 'Косметология', 'Массаж', 'Брови и ресницы']
        },
        {
            'name': 'Медицина',
            'subtypes': ['Стоматология', 'Медицинский центр', 'Диагностика', 'Физиотерапия', 'Психология']
        },
        {
            'name': 'Фитнес',
            'subtypes': ['Спортивный зал', 'Йога', 'Плавание', 'Танцы', 'Боевые искусства']
        },
        {
            'name': 'Образование',
            'subtypes': ['Языковая школа', 'Курсы', 'Репетиторство', 'Детский сад', 'Учебный центр']
        },
        {
            'name': 'Другое',
            'subtypes': ['Консультации', 'Ремонт', 'Услуги', 'Торговля', 'Производство']
        }
    ]
    
    created_types = []
    
    for type_data in types_data:
        # Создаем тип бизнеса
        business_type, created = BusinessType.objects.get_or_create(
            name=type_data['name']
        )
        
        if created:
            print(f"✅ Создан тип бизнеса: {business_type.name}")
        else:
            print(f"ℹ️  Тип бизнеса уже существует: {business_type.name}")
        
        created_types.append(business_type)
        
        # Создаем подтипы
        for subtype_name in type_data['subtypes']:
            subtype, created = BusinessSubtype.objects.get_or_create(
                business_type=business_type,
                name=subtype_name
            )
            
            if created:
                print(f"  ✅ Создан подтип: {subtype.name}")
            else:
                print(f"  ℹ️  Подтип уже существует: {subtype.name}")
    
    print(f"\n🎉 Всего создано типов бизнеса: {len(created_types)}")
    
    # Выводим список всех типов для использования в форме
    print("\n📋 Список типов бизнеса для формы регистрации:")
    for business_type in BusinessType.objects.all():
        print(f"  {business_type.id}: {business_type.name}")

if __name__ == '__main__':
    create_business_types() 