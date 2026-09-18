"""
Serializadores DRF para el módulo de tareas.
Valida y transforma datos del tablero Kanban.

Se usan `serializers.Serializer` simples (no ModelSerializer) porque
`Tarea` es un documento de MongoEngine, no un modelo del ORM de Django.
"""
from rest_framework import serializers
from .modelo import Tarea


class TareaSerializador(serializers.Serializer):
    """Serializador para operaciones CRUD de tareas."""

    titulo = serializers.CharField(max_length=200)
    descripcion = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=''
    )
    estado = serializers.ChoiceField(
        choices=['por_hacer', 'en_progreso', 'completado'],
        default='por_hacer'
    )
    etiqueta = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=''
    )
    color_etiqueta = serializers.CharField(
        max_length=7, required=False, default='#00E5FF'
    )
    fecha_limite = serializers.DateField(required=False, allow_null=True)
    proyecto = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=''
    )

    def validate_titulo(self, valor):
        """Valida que el título no esté vacío después de recortar espacios."""
        if not valor.strip():
            raise serializers.ValidationError("El título no puede estar vacío.")
        return valor.strip()

    def create(self, datos_validados):
        """Crea el documento de tarea en MongoDB."""
        tarea = Tarea(**datos_validados)
        tarea.save()
        return tarea

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
            'titulo': instancia.titulo,
            'descripcion': instancia.descripcion or '',
            'estado': instancia.estado,
            'etiqueta': instancia.etiqueta or '',
            'color_etiqueta': instancia.color_etiqueta,
            'fecha_limite': (
                instancia.fecha_limite.isoformat()
                if instancia.fecha_limite else None
            ),
            'origen_nodo': instancia.origen_nodo or '',
            'proyecto': instancia.proyecto or '',
            'usuario': str(instancia.usuario.id),
            'fecha_creacion': (
                instancia.fecha_creacion.isoformat()
                if instancia.fecha_creacion else None
            ),
        }

class MoverTareaSerializador(serializers.Serializer):
    """Serializador para mover tarea entre columnas (RF-TAR-05)."""
    estado = serializers.ChoiceField(
        choices=['por_hacer', 'en_progreso', 'completado']
    )