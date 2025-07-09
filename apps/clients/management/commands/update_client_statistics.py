from django.core.management.base import BaseCommand
from apps.clients.models import Client


class Command(BaseCommand):
    help = 'Обновляет статистику всех клиентов на основе записей'

    def add_arguments(self, parser):
        parser.add_argument(
            '--business',
            type=int,
            help='ID бизнеса для обновления статистики только его клиентов',
        )

    def handle(self, *args, **options):
        business_id = options.get('business')
        
        if business_id:
            clients = Client.objects.filter(business_id=business_id)
            self.stdout.write(f'Обновление статистики для клиентов бизнеса {business_id}...')
        else:
            clients = Client.objects.all()
            self.stdout.write('Обновление статистики для всех клиентов...')
        
        updated_count = 0
        total_count = clients.count()
        
        for client in clients:
            try:
                client.update_statistics()
                updated_count += 1
                self.stdout.write(f'Обновлен клиент: {client.name} (ID: {client.id})')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка обновления клиента {client.name} (ID: {client.id}): {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Статистика обновлена для {updated_count} из {total_count} клиентов'
            )
        ) 