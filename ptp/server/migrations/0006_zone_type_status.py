# Generated migration: Zone.zone_type, Zone.status

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0005_zone_cleanup_periodic_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='zone',
            name='zone_type',
            field=models.CharField(
                choices=[('regular', 'Обычная'), ('pss', 'ПСС (закладки запрещены)')],
                default='regular',
                max_length=16,
                verbose_name='Тип зоны',
            ),
        ),
        migrations.AddField(
            model_name='zone',
            name='status',
            field=models.CharField(
                choices=[('approved', 'Одобрена'), ('pending', 'На модерации')],
                default='approved',
                max_length=16,
                verbose_name='Статус модерации',
            ),
        ),
    ]
