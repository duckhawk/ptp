# Initial migration: Zone model

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.JSONField(help_text='Список точек [[lat, lng], ...], минимум 2 точки')),
                ('date', models.DateField(blank=True, null=True, verbose_name='Дата закладки')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Зона',
                'verbose_name_plural': 'Зоны',
            },
        ),
    ]
