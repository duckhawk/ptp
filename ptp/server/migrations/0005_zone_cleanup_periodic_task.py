# Data migration: периодическая задача зачистки зон, помеченных к удалению

from django.db import migrations


def create_cleanup_periodic_task(apps, schema_editor):
    IntervalSchedule = apps.get_model('django_celery_beat', 'IntervalSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    # Расписание: раз в 1 день
    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=1,
        period=IntervalSchedule.DAYS,
    )
    PeriodicTask.objects.get_or_create(
        name='Зачистка зон, помеченных к удалению',
        defaults={
            'interval': schedule,
            'task': 'server.tasks.cleanup_zones_marked_for_deletion',
            'enabled': True,
        },
    )


def remove_cleanup_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    PeriodicTask.objects.filter(
        name='Зачистка зон, помеченных к удалению',
        task='server.tasks.cleanup_zones_marked_for_deletion',
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0004_zone_marked_for_deletion_delete_after'),
        ('django_celery_beat', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_cleanup_periodic_task, remove_cleanup_periodic_task),
    ]
