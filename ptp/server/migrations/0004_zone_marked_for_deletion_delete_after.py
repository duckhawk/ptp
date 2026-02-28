# Migration: Zone — отложенное удаление

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0003_zone_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='zone',
            name='marked_for_deletion',
            field=models.BooleanField(default=False, verbose_name='К удалению'),
        ),
        migrations.AddField(
            model_name='zone',
            name='delete_after',
            field=models.DateField(blank=True, null=True, verbose_name='Удалить после'),
        ),
    ]
