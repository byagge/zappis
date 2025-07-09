from django.urls import path
from .views import ClientListCreateAPIView, ClientRetrieveUpdateDestroyAPIView, clients_page, ClientExportAPIView
 
urlpatterns = [
    path('', clients_page, name='clients-page'),
    path('api/clients/', ClientListCreateAPIView.as_view(), name='client-list-create'),
    path('api/clients/<int:pk>/', ClientRetrieveUpdateDestroyAPIView.as_view(), name='client-detail'),
    path('api/export/', ClientExportAPIView.as_view(), name='client-export'),
] 