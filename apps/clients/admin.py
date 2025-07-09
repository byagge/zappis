from django.contrib import admin
from .models import Client

# Register your models here.

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "email", "status", "city", "business", "total_visits", "total_spent", "created_at")
    list_filter = ("status", "city", "business")
    search_fields = ("name", "phone", "email")
    ordering = ("-created_at",)
