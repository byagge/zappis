from django.core.management.base import BaseCommand
from apps.schedules.signals import send_reminder_notifications

class Command(BaseCommand):
    help = 'Отправка напоминаний о предстоящих записях (за день и за 2 часа)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительная отправка всех напоминаний',
        )

    def handle(self, *args, **options):
        if options['force']:
            self.stdout.write('Принудительная отправка всех напоминаний...')
        else:
            self.stdout.write('Отправка напоминаний...')
            
        send_reminder_notifications()
        self.stdout.write(self.style.SUCCESS('Напоминания отправлены'))
        
        self.stdout.write('\n💡 Для автоматических напоминаний настройте cron:')
        self.stdout.write('   # Каждые 5 минут для напоминаний за 2 часа')
        self.stdout.write('   */5 * * * * cd /path/to/project && python manage.py send_reminders')
        self.stdout.write('   # Каждый день в 9:00 для напоминаний за день')
        self.stdout.write('   0 9 * * * cd /path/to/project && python manage.py send_reminders') 