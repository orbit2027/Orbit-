"""
Serializadores DRF para el módulo de usuarios.
Validan y transforman datos de entrada/salida de la API.
"""
import re
from rest_framework import serializers
from .modelo import Usuario

class RegistroUsuarioSerializador(serializers.Serializer):
 
    nombre_completo = serializers.CharField(max_length=150)
    correo = serializers.EmailField(max_length=254)
    contrasena = serializers.CharField(min_length=8, write_only=True)

    def validate_correo(self, valor):
        if Usuario.objects(correo=valor).first():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return valor.lower().strip()

    def validate_contrasena(self, valor):
       
        if not re.search(r'[A-Z]', valor):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una mayúscula."
            )
        if not re.search(r'\d', valor):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )
        return valor

    def create(self, validated_data):
        """Crea un nuevo usuario con la contraseña cifrada."""
        usuario = Usuario(
            nombre_completo=validated_data['nombre_completo'],
            correo=validated_data['correo'],
            rol='usuario'
        )
        usuario.set_contrasena(validated_data['contrasena'])
        usuario.save()
        return usuario


class LoginUsuarioSerializador(serializers.Serializer):
    """Serializador para inicio de sesión (RF-USU-02)."""
    correo = serializers.EmailField()
    contrasena = serializers.CharField()


class PerfilUsuarioSerializador(serializers.Serializer):
    """Serializador para visualizar perfil de usuario compatible con MongoEngine.

    Usamos un Serializer simple porque `Usuario` es un documento de MongoEngine
    y `ModelSerializer` intenta acceder a metadatos de modelos Django.
    """
    nombre_completo = serializers.CharField()
    correo = serializers.EmailField()
    fecha_registro = serializers.DateTimeField()

    def to_representation(self, obj):
        return {
            'id': str(obj.id),
            'nombre_completo': getattr(obj, 'nombre_completo', ''),
            'correo': getattr(obj, 'correo', ''),
            'rol': getattr(obj, 'rol', 'usuario'),
            'fecha_registro': getattr(obj, 'fecha_registro', None),
        }


class EditarUsuarioSerializador(serializers.Serializer):
    """
    Serializador para editar perfil de usuario (RF-USU-04).
    Permite modificar nombre, correo y contraseña (con confirmación).
    """
    nombre_completo = serializers.CharField(max_length=150, required=False)
    correo = serializers.EmailField(max_length=254, required=False)
    contrasena_actual = serializers.CharField(required=False)
    contrasena_nueva = serializers.CharField(min_length=8, required=False)

    def validate_correo(self, valor):
        """Verifica que el nuevo correo no esté en uso por otro usuario."""
        usuario_actual = self.context.get('usuario_actual')
        if Usuario.objects(correo=valor, id__ne=usuario_actual.id).first():
            raise serializers.ValidationError("Este correo ya está en uso.")
        return valor.lower().strip()

    def validate_contrasena_nueva(self, valor):
        """Valida fortaleza de la nueva contraseña si se proporciona."""
        if not re.search(r'[A-Z]', valor):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una mayúscula."
            )
        if not re.search(r'\d', valor):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )
        return valor


class EliminarCuentaSerializador(serializers.Serializer):
    """
    Serializador para eliminación de cuenta (RF-USU-05).
    Requiere confirmación de contraseña antes de eliminar.
    """
    contrasena = serializers.CharField()

    def validate_contrasena(self, valor):
        """Verifica que la contraseña proporcionada sea correcta."""
        usuario = self.context.get('usuario_actual')
        if not usuario.verificar_contrasena(valor):
            raise serializers.ValidationError("Contraseña incorrecta.")
        return valor