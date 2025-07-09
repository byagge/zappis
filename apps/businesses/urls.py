from django.urls import path
from .views import business_type_list, business_subtype_list, BusinessWorkingHourView
 
urlpatterns = [
    path('api/business-types/', business_type_list, name='business-type-list'),
    path('api/business-subtypes/', business_subtype_list, name='business-subtype-list'),
    path('api/business-working-hours/', BusinessWorkingHourView.as_view(), name='business-working-hours'),
] 