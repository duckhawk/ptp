from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Zone
from .serializers import ZoneSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def current_user(request):
    """Возвращает информацию о текущем пользователе и устанавливает CSRF cookie."""
    if request.user.is_authenticated:
        display_name = f'{request.user.first_name} {request.user.last_name}'.strip()
        if not display_name:
            display_name = request.user.username
        return Response({
            'is_authenticated': True,
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'display_name': display_name,
            'is_staff': request.user.is_staff,
        })
    return Response({'is_authenticated': False})


@method_decorator(ensure_csrf_cookie, name='list')
class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    permission_classes = [IsAuthenticated]
