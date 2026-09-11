"""
Serializadores DRF para el módulo de proyectos.
Se usan serializers.Serializer simples (no ModelSerializer) porque
Proyecto es un documento de MongoEngine, no un modelo del ORM de Django.
"""
from rest_framework import serializers
from .modelo import Proyecto


class ProyectoSerializador(serializers.Serializer):
    """Serializador para operaciones CRUD de proyectos."""

    nombre = serializers.CharField(max_length=150)
    descripcion = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=''
    )
    color = serializers.CharField(
        max_length=7, required=False, default='#00E5FF'
    )
    estado = serializers.ChoiceField(
        choices=['activo', 'archivado'], default='activo'
    )
    fecha_limite = serializers.DateField(required=False, allow_null=True)

    def validate_nombre(self, valor):
        """Valida que el nombre no esté vacío tras recortar espacios."""
        if not valor.strip():
            raise serializers.ValidationError(
                "El nombre del proyecto no puede estar vacío."
            )
        return valor.strip()

    def create(self, datos_validados):
        """Crea el documento de proyecto en la base de datos."""
        proyecto = Proyecto(**datos_validados)
        proyecto.save()
        return proyecto

    def update(self, instancia, datos_validados):
        """Actualiza solo los campos enviados en la petición."""
        for campo, valor in datos_validados.items():
            setattr(instancia, campo, valor)
        instancia.save()
        return instancia

    def to_representation(self, instancia):
        """Convierte el documento MongoEngine a JSON para el frontend."""
        return {
            'id': str(instancia.id),
            'nombre': instancia.nombre,
            'descripcion': instancia.descripcion or '',
            'color': instancia.color,
            'estado': instancia.estado,
            'fecha_limite': (
                instancia.fecha_limite.isoformat()
                if instancia.fecha_limite else None
            ),
            'fecha_creacion': (
                instancia.fecha_creacion.isoformat()
                if instancia.fecha_creacion else None
            ),
        }