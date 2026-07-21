from django.conf import settings
from django.db import models


class Zone(models.Model):
    """
    Зона на карте — полигон из списка точек [широта, долгота].
    """

    ZONE_TYPE_REGULAR = 'regular'
    ZONE_TYPE_PSS = 'pss'
    ZONE_TYPE_CHOICES = [
        (ZONE_TYPE_REGULAR, 'Обычная'),
        (ZONE_TYPE_PSS, 'ПСС (закладки запрещены)'),
    ]

    STATUS_APPROVED = 'approved'
    STATUS_PENDING = 'pending'
    STATUS_CHOICES = [
        (STATUS_APPROVED, 'Одобрена'),
        (STATUS_PENDING, 'На модерации'),
    ]

    points = models.JSONField(
        help_text='Список точек [[lat, lng], ...], минимум 2 точки'
    )
    date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата закладки'
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='Примечания'
    )
    zone_type = models.CharField(
        max_length=16,
        choices=ZONE_TYPE_CHOICES,
        default=ZONE_TYPE_REGULAR,
        verbose_name='Тип зоны'
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_APPROVED,
        verbose_name='Статус модерации'
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='zones',
        verbose_name='Создатель',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Отложенное удаление
    marked_for_deletion = models.BooleanField(
        default=False,
        verbose_name='К удалению'
    )
    delete_after = models.DateField(
        null=True,
        blank=True,
        verbose_name='Удалить после'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Зона'
        verbose_name_plural = 'Зоны'

    def __str__(self):
        return f'Зона {self.id} ({self.date})'
