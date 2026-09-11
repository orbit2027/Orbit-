import re
from rest_framework import serializers
from apps.usuarios.modelo import Usuario


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
    contrasena = serializers.CharField(min_length=8)
    rol = serializers.ChoiceField(choices=['usuario', 'administrador'], default='usuario')

    def validate_correo(self, valor):
        if Usuario.objects(correo=valor).first():
            raise serializers.ValidationError("Este correo ya esta registrado.")
        return valor.lower().strip()

    def validate_contrasena(self, valor):
        if not re.search(r'[A-Z]', valor):
            raise serializers.ValidationError("La contrasena debe tener al menos una mayuscula.")
        if not re.search(r'\d', valor):
            raise serializers.ValidationError("La contrasena debe tener al menos un numero.")
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
        if Usuario.objects(correo=valor, id__ne=usuario_id).first():
            raise serializers.ValidationError("Este correo ya esta en uso.")
        return valor.lower().strip()
