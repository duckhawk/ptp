from rest_framework import serializers
from .models import Zone


class ZoneSerializer(serializers.ModelSerializer):
    creator_id = serializers.IntegerField(read_only=True)
    creator_display_name = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = ['id', 'points', 'date', 'notes', 'created_at', 'creator_id', 'creator_display_name']
        read_only_fields = ['id', 'created_at', 'creator_id', 'creator_display_name']

    def get_creator_display_name(self, obj):
        if not obj.creator_id:
            return None
        creator = obj.creator
        if not creator:
            return None
        name = f'{creator.first_name} {creator.last_name}'.strip()
        return name or creator.username

    def validate_points(self, value):
        if not value or not isinstance(value, list):
            raise serializers.ValidationError('points должен быть непустым списком')
        if len(value) < 2:
            raise serializers.ValidationError('Минимум 2 точки для зоны')
        for i, pt in enumerate(value):
            if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                raise serializers.ValidationError(f'Точка {i}: ожидается [lat, lng]')
            try:
                lat, lng = float(pt[0]), float(pt[1])
                if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                    raise serializers.ValidationError(f'Точка {i}: неверные координаты')
            except (TypeError, ValueError):
                raise serializers.ValidationError(f'Точка {i}: числа lat, lng')
        return value
