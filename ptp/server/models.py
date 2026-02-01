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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Зона'
        verbose_name_plural = 'Зоны'

    def __str__(self):
        return f'Зона {self.id} ({self.date})'
