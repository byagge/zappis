# Generated by Django 5.2.3 on 2025-06-27 02:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('reminder', 'Напоминание'), ('event', 'Событие'), ('alert', 'Оповещение'), ('system', 'Системное')], default='reminder', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('date', models.DateTimeField()),
                ('is_read', models.BooleanField(default=False)),
                ('is_important', models.BooleanField(default=False)),
                ('reminder_time', models.CharField(blank=True, max_length=100, null=True)),
                ('event_date', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
