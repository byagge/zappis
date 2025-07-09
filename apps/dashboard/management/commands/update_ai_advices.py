from django.core.management.base import BaseCommand
from apps.businesses.models import Business
from apps.dashboard.models import AIAdvice
from apps.dashboard.utils import generate_ai_advices

class Command(BaseCommand):
    help = 'Обновляет ИИ-советы для всех активных бизнесов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно обновить советы, даже если они не устарели',
        )

    def handle(self, *args, **options):
        force_update = options['force']
        
        self.stdout.write('Обновление ИИ-советов...')
        
        businesses = Business.objects.filter(is_active=True)
        
        if not businesses.exists():
            self.stdout.write(self.style.WARNING('Нет активных бизнесов'))
            return
        
        updated_count = 0
        
        for business in businesses:
            try:
                advice_obj = AIAdvice.objects.filter(business=business).first()
                
                # Проверяем, нужно ли обновление
                need_update = (
                    not advice_obj or 
                    advice_obj.is_outdated() or 
                    force_update
                )
                
                if need_update:
                    self.stdout.write(f'Обновление советов для {business.name}...')
                    
                    # Генерируем новые советы
                    new_advices = generate_ai_advices(business)
                    
                    if advice_obj:
                        # Обновляем существующие советы
                        advice_obj.data = new_advices
                        advice_obj.save()
                        self.stdout.write(f'  ✓ Обновлены существующие советы')
                    else:
                        # Создаем новые советы
                        AIAdvice.objects.create(
                            business=business,
                            data=new_advices
                        )
                        self.stdout.write(f'  ✓ Созданы новые советы')
                    
                    updated_count += 1
                else:
                    self.stdout.write(f'Советы для {business.name} актуальны (обновлены {advice_obj.updated_at.strftime("%d.%m.%Y")})')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при обновлении советов для {business.name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Обновление завершено! Обновлено бизнесов: {updated_count}'
            )
        ) 