# Generated migration: Zone.notes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0002_zone_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='zone',
            name='notes',
            field=models.TextField(blank=True, default='', verbose_name='Примечания'),
        ),
    ]
