from django.contrib import admin
from .models import Zone


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'marked_for_deletion', 'delete_after', 'created_at', 'points_preview')
    list_filter = ('date', 'marked_for_deletion', 'created_at')
    readonly_fields = ('created_at',)

    def points_preview(self, obj):
        if not obj.points:
            return '—'
        return f'{len(obj.points)} точек'

    points_preview.short_description = 'Точек'
