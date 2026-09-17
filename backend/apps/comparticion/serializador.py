"""
Serializadores DRF para el módulo de compartición.
"""
from rest_framework import serializers
from .modelo import Comparticion


class ComparticionSerializador(serializers.Serializer):
    """Serializador para crear/editar una compartición."""

    correo = serializers.EmailField()
    tipo_objeto = serializers.ChoiceField(choices=['tarea', 'proyecto'])
    objeto_id = serializers.CharField(max_length=50)
    permiso = serializers.ChoiceField(
        choices=['ver', 'editar', 'administrar'], default='ver'
    )


class PermisoSerializador(serializers.Serializer):
    """Serializador para cambiar el permiso de una compartición."""
    permiso = serializers.ChoiceField(choices=['ver', 'editar', 'administrar'])


class ComparticionSalidaSerializador(serializers.Serializer):
    """Serializador de salida: detalles legibles de la compartición."""

    def to_representation(self, instancia):
        return {
            'id': str(instancia.id),
            'tipo_objeto': instancia.tipo_objeto,
            'objeto_id': instancia.objeto_id,
            'permiso': instancia.permiso,
            'correo': instancia.compartido_con.correo,
            'nombre': instancia.compartido_con.nombre_completo,
            'fecha_compartida': (
                instancia.fecha_compartida.isoformat()
                if instancia.fecha_compartida else None
            ),
        }


class ComparticionConmigoSalidaSerializador(ComparticionSalidaSerializador):
    """Compartición recibida, con título del objeto y propietario legibles."""
    titulo = serializers.CharField()
    propietario = serializers.CharField()