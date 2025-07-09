import json
from .models import Client
from apps.clients.serializers import ClientSerializer

def export_clients(queryset, export_format):
    if export_format == 'json':
        data = ClientSerializer(queryset, many=True).data
        return json.dumps(data, ensure_ascii=False, indent=2), 'application/json'
    else:
        raise ValueError('Only JSON format is supported') 