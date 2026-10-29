from rest_framework import serializers
from apps.usuarios.modelo import Usuario
from .politica_contrasena import validar_contrasena


class UsuarioAdminSerializador(serializers.Serializer):
    """
    Serializador para visualizar usuarios en el panel admin.
    Solo salida: convierte documentos MongoEngine a JSON.
    """

    def to_representation(self, instancia):
        return {
            'id': str(instancia.id),
            'nombre_completo': instancia.nombre_completo,
            'correo': instancia.correo,
            'rol': instancia.rol,
            'activo': bool(instancia.activo),
            'fecha_registro': (
                instancia.fecha_registro.isoformat()
                if instancia.fecha_registro else None
            ),
        }


class CrearUsuarioAdminSerializador(serializers.Serializer):
    nombre_completo = serializers.CharField(max_length=150)
    correo = serializers.EmailField(max_length=254)
    contrasena = serializers.CharField()
    rol = serializers.ChoiceField(choices=['usuario', 'administrador'], default='usuario')

    def validate_correo(self, valor):
        if Usuario.objects.filter(correo=valor).first():
            raise serializers.ValidationError("Este correo ya esta registrado.")
        return valor.lower().strip()

    def validate_contrasena(self, valor):
        errores = validar_contrasena(valor)
        if errores:
            raise serializers.ValidationError(errores)
        return valor

    def create(self, validated_data):
        usuario = Usuario(
            nombre_completo=validated_data['nombre_completo'],
            correo=validated_data['correo'],
            rol=validated_data.get('rol', 'usuario')
        )
        usuario.set_contrasena(validated_data['contrasena'])
        usuario.save()
        return usuario


class EditarUsuarioAdminSerializador(serializers.Serializer):
    nombre_completo = serializers.CharField(max_length=150, required=False)
    correo = serializers.EmailField(max_length=254, required=False)
    rol = serializers.ChoiceField(choices=['usuario', 'administrador'], required=False)

    def validate_correo(self, valor):
        usuario_id = self.context.get('usuario_id')
        if Usuario.objects.filter(correo=valor).exclude(id=usuario_id).first():
            raise serializers.ValidationError("Este correo ya esta en uso.")
        return valor.lower().strip()


# ── Serializadores de salida (documentación OpenAPI) ──────────────────────

class CrecimientoMensualSerializador(serializers.Serializer):
    """Registros nuevos en un mes."""
    mes = serializers.CharField()
    registros = serializers.IntegerField()


class EstadisticasGlobalesSerializador(serializers.Serializer):
    """Métricas globales del sistema."""
    total_usuarios = serializers.IntegerField()
    usuarios_activos = serializers.IntegerField()
    tareas_activas = serializers.IntegerField()
    completadas_hoy = serializers.IntegerField()
    activos_hoy = serializers.IntegerField()
    proyectos_totales = serializers.IntegerField()
    proyectos_activos = serializers.IntegerField()
    proyectos_archivados = serializers.IntegerField()
    crecimiento_mensual = CrecimientoMensualSerializador(many=True)


class ToggleUsuarioRespuestaSerializador(serializers.Serializer):
    """Resultado de activar/desactivar un usuario."""
    mensaje = serializers.CharField()
    activo = serializers.BooleanField()


class ConfiguracionAdminSerializador(serializers.Serializer):
    aviso_global = serializers.CharField(max_length=500, allow_blank=True, required=False)
    mantenimiento_activo = serializers.BooleanField(required=False)
    mensaje_mantenimiento = serializers.CharField(max_length=500, required=False)
    longitud_minima_contrasena = serializers.IntegerField(
        min_value=8, max_value=128, required=False
    )
    exigir_mayuscula = serializers.BooleanField(required=False)
    exigir_numero = serializers.BooleanField(required=False)

    def validate(self, datos):
        mantenimiento_activo = datos.get(
            'mantenimiento_activo',
            getattr(self.instance, 'mantenimiento_activo', False),
        )
        mensaje = datos.get(
            'mensaje_mantenimiento',
            getattr(self.instance, 'mensaje_mantenimiento', ''),
        )
        if mantenimiento_activo and not mensaje.strip():
            raise serializers.ValidationError({
                'mensaje_mantenimiento': (
                    'Escribe el aviso que se mostrará durante el mantenimiento.'
                )
            })
        return datos


class PoliticaContrasenaSerializador(serializers.Serializer):
    longitud_minima = serializers.IntegerField()
    mayuscula_requerida = serializers.BooleanField()
    numero_requerido = serializers.BooleanField()


class ConfiguracionPublicaSerializador(serializers.Serializer):
    aviso_global = serializers.CharField()
    mantenimiento_activo = serializers.BooleanField()
    mensaje_mantenimiento = serializers.CharField()
    politica_contrasena = PoliticaContrasenaSerializador()


class TareaModeracionAdminSerializador(serializers.Serializer):
    """Tarea disponible para moderación global, con datos de su propietario."""
    id = serializers.CharField()
    titulo = serializers.CharField()
    descripcion = serializers.CharField()
    estado = serializers.CharField()
    etiqueta = serializers.CharField()
    fecha_limite = serializers.DateField(allow_null=True)
    propietario = serializers.CharField()
    correo_propietario = serializers.EmailField()


class ProyectoModeracionAdminSerializador(serializers.Serializer):
    """Proyecto disponible para moderación global, con sus métricas."""
    id = serializers.CharField()
    nombre = serializers.CharField()
    descripcion = serializers.CharField()
    estado = serializers.CharField()
    fecha_limite = serializers.DateField(allow_null=True)
    propietario = serializers.CharField()
    correo_propietario = serializers.EmailField()
    tareas_totales = serializers.IntegerField()
    tareas_completadas = serializers.IntegerField()
