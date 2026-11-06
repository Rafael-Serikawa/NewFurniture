"""API REST do NewFurniture (Django REST Framework)."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Usuario

T = Usuario.Tipo


@api_view(['GET'])
@permission_classes([AllowAny])
def status_api(request):
    return Response({'sistema': 'NewFurniture', 'status': 'ok'})
