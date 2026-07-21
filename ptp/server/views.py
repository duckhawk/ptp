from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta, datetime
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
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
    queryset = Zone.objects.select_related('creator').all()
    serializer_class = ZoneSerializer

    def get_permissions(self):
        # Просмотр зон доступен всем (в т.ч. анонимам).
        # Создание/изменение/модерация — только авторизованным (staff проверяется отдельно).
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Zone.objects.select_related('creator').all()
        user = self.request.user
        # Администраторы видят все зоны, включая ожидающие модерации.
        if user.is_authenticated and user.is_staff:
            return qs
        # Остальные видят только одобренные зоны и собственные предложения на модерации.
        if user.is_authenticated:
            return qs.filter(Q(status=Zone.STATUS_APPROVED) | Q(creator=user))
        return qs.filter(status=Zone.STATUS_APPROVED)

    def perform_create(self, serializer):
        user = self.request.user
        # Зоны от администраторов сразу одобрены, от остальных — уходят на модерацию.
        status = Zone.STATUS_APPROVED if user.is_staff else Zone.STATUS_PENDING
        serializer.save(creator=user, status=status)

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied('Редактировать зоны могут только администраторы и staff.')
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied('Удалять зоны могут только администраторы и staff.')
        instance = self.get_object()
        # Отложенное удаление: помечаем зону и дату удаления
        delete_after_str = request.query_params.get('delete_after') or (getattr(request, 'data', None) or {}).get('delete_after')
        if delete_after_str:
            try:
                delete_after = datetime.strptime(delete_after_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                delete_after = timezone.now().date() + timedelta(days=7)
        else:
            delete_after = timezone.now().date() + timedelta(days=7)
        instance.marked_for_deletion = True
        instance.delete_after = delete_after
        instance.save(update_fields=['marked_for_deletion', 'delete_after'])
        return Response(status=204)

    @action(detail=True, methods=['post'], url_path='delete-immediately')
    def delete_immediately(self, request, pk=None):
        """Удалить зону сразу (без отложенного удаления)."""
        if not request.user.is_staff:
            raise PermissionDenied('Удалять зоны могут только администраторы и staff.')
        instance = self.get_object()
        instance.delete()
        return Response(status=204)

    @action(detail=True, methods=['post'], url_path='cancel-deletion')
    def cancel_deletion(self, request, pk=None):
        """Снять пометку «к удалению» с зоны."""
        if not request.user.is_staff:
            raise PermissionDenied('Только администраторы и staff.')
        instance = self.get_object()
        instance.marked_for_deletion = False
        instance.delete_after = None
        instance.save(update_fields=['marked_for_deletion', 'delete_after'])
        return Response(status=204)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Одобрить зону, предложенную на модерацию."""
        if not request.user.is_staff:
            raise PermissionDenied('Модерировать зоны могут только администраторы и staff.')
        instance = self.get_object()
        instance.status = Zone.STATUS_APPROVED
        instance.save(update_fields=['status'])
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Отклонить зону, предложенную на модерацию (удалить)."""
        if not request.user.is_staff:
            raise PermissionDenied('Модерировать зоны могут только администраторы и staff.')
        instance = self.get_object()
        instance.delete()
        return Response(status=204)
