from celery import shared_task
from django.utils import timezone


@shared_task
def example_task(x, y):
    """Пример задачи Celery: сложение двух чисел."""
    return x + y


@shared_task
def cleanup_zones_marked_for_deletion():
    """
    Удаляет зоны, помеченные к удалению, у которых delete_after <= сегодня.
    Вызывается по расписанию (раз в сутки).
    """
    from .models import Zone
    today = timezone.now().date()
    deleted_count, _ = Zone.objects.filter(
        marked_for_deletion=True,
        delete_after__lte=today,
    ).delete()
    return deleted_count
