from django.conf import settings
from django.db import models


class Zone(models.Model):
    """
    Зона на карте — полигон из списка точек [широта, долгота].
    """
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
        ordering = ['-created_at']
        verbose_name = 'Зона'
        verbose_name_plural = 'Зоны'

    def __str__(self):
        return f'Зона {self.id} ({self.date})'
