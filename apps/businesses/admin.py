from django.contrib import admin
from .models import BusinessType, BusinessSubtype, Business, BusinessPhoto, BusinessWorkingHour

admin.site.register(BusinessType)
admin.site.register(BusinessSubtype)
admin.site.register(Business)
admin.site.register(BusinessPhoto)

class BusinessWorkingHourAdmin(admin.ModelAdmin):
    list_display = ('business', 'day', 'start', 'end', 'enabled')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(day_order=BusinessWorkingHour.get_week_ordering()).order_by('business', 'day_order')

admin.site.register(BusinessWorkingHour, BusinessWorkingHourAdmin)
