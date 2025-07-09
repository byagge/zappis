from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BusinessRegisterSerializer
from django.http import JsonResponse
from .models import BusinessType, BusinessSubtype, Business, BusinessWorkingHour
from .serializers import BusinessWorkingHourSerializer
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Create your views here.

class BusinessRegisterView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BusinessRegisterSerializer(data=request.data)
        if serializer.is_valid():
            business = serializer.save()
            return Response(BusinessRegisterSerializer(business).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def business_type_list(request):
    types = list(BusinessType.objects.values('id', 'name'))
    return JsonResponse({'types': types})

def business_subtype_list(request):
    business_type_id = request.GET.get('business_type_id')
    subtypes = BusinessSubtype.objects.filter(business_type_id=business_type_id).values('id', 'name')
    return JsonResponse({'subtypes': list(subtypes)})

@method_decorator(csrf_exempt, name='dispatch')
class BusinessWorkingHourView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        business_id = request.GET.get('business_id')
        if not business_id:
            return Response({'detail': 'business_id required'}, status=400)
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            return Response({'detail': 'Business not found'}, status=404)
        hours = BusinessWorkingHour.objects.filter(business=business)
        serializer = BusinessWorkingHourSerializer(hours, many=True)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        business_id = request.data.get('business_id')
        if not business_id:
            return Response({'detail': 'business_id required'}, status=400)
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            return Response({'detail': 'Business not found'}, status=404)
        data = request.data.get('working_hours', [])
        # Обновляем или создаём по дням недели
        for item in data:
            obj, _ = BusinessWorkingHour.objects.update_or_create(
                business=business, day=item['day'],
                defaults={
                    'start': item['start'],
                    'end': item['end'],
                    'enabled': item['enabled']
                }
            )
        hours = BusinessWorkingHour.objects.filter(business=business)
        serializer = BusinessWorkingHourSerializer(hours, many=True)
        return Response(serializer.data)
