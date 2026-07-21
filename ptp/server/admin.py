from django.contrib import admin
from .models import Zone


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'zone_type', 'status', 'marked_for_deletion', 'delete_after', 'created_at', 'points_preview')
    list_filter = ('zone_type', 'status', 'date', 'marked_for_deletion', 'created_at')
    readonly_fields = ('created_at',)
    actions = ('approve_zones',)

    def points_preview(self, obj):
        if not obj.points:
            return '—'
        return f'{len(obj.points)} точек'

    points_preview.short_description = 'Точек'

    @admin.action(description='Одобрить выбранные зоны')
    def approve_zones(self, request, queryset):
        updated = queryset.update(status=Zone.STATUS_APPROVED)
        self.message_user(request, f'Одобрено зон: {updated}')
