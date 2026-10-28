"""
Serializadores DRF para el módulo de compartición.
"""
from rest_framework import serializers

from apps.usuarios.modelo import Usuario

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


class RespuestaInvitacionSerializador(serializers.Serializer):
    """Serializador para aceptar o rechazar una invitación."""
    aceptar = serializers.BooleanField()


def _nombre_visible(usuario, correo):
    """Nombre a mostrar: el del usuario registrado o el correo."""
    if usuario and usuario.nombre_completo:
        return usuario.nombre_completo
    return correo


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
            'estado': 'aceptada',
            'origen': 'comparticion',
            'fecha_compartida': (
                instancia.fecha_compartida.isoformat()
                if instancia.fecha_compartida else None
            ),
        }


class InvitacionSalidaSerializador(serializers.Serializer):
    """Invitación pendiente o respondida, vista por quien comparte."""

    def to_representation(self, instancia):
        usuario = Usuario.objects.filter(correo__iexact=instancia.correo).first()
        return {
            'id': str(instancia.id),
            'tipo_objeto': instancia.tipo_objeto,
            'objeto_id': instancia.objeto_id,
            'permiso': instancia.permiso,
            'correo': instancia.correo,
            'nombre': _nombre_visible(usuario, instancia.correo),
            'estado': instancia.estado,
            'origen': 'invitacion',
            'tiene_cuenta': usuario is not None,
            'fecha_compartida': (
                instancia.fecha_creacion.isoformat()
                if instancia.fecha_creacion else None
            ),
        }


class InvitacionRecibidaSalidaSerializador(InvitacionSalidaSerializador):
    """Invitación recibida por el usuario autenticado."""

    def to_representation(self, instancia):
        datos = super().to_representation(instancia)
        datos.update({
            'titulo': instancia.objeto_titulo,
            'propietario': (
                instancia.propietario.nombre_completo
                or instancia.propietario.correo
            ),
            'token': str(instancia.token),
        })
        return datos


class ComparticionConmigoSalidaSerializador(ComparticionSalidaSerializador):
    """Compartición recibida, con título del objeto y propietario legibles."""
    titulo = serializers.CharField()
    propietario = serializers.CharField()
