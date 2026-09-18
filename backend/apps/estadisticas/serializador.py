"""
Serializadores de salida del módulo de estadísticas (documentación OpenAPI).
"""
from rest_framework import serializers


class SemanaEstadisticaSerializador(serializers.Serializer):
    """Métricas de una semana."""
    semana = serializers.CharField()
    creadas = serializers.IntegerField()
    completadas = serializers.IntegerField()


class EstadisticasUsuarioSerializador(serializers.Serializer):
    """Métricas individuales de productividad del usuario."""
    total = serializers.IntegerField()
    por_hacer = serializers.IntegerField()
    en_progreso = serializers.IntegerField()
    completadas = serializers.IntegerField()
    semanal = SemanaEstadisticaSerializador(many=True)