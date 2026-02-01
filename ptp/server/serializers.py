from rest_framework import serializers
from .models import Zone


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ['id', 'points', 'date', 'created_at']
        read_only_fields = ['id', 'created_at']

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
