"""
Serializadores DRF para el módulo de restablecimiento de contraseña.
"""
from rest_framework import serializers
from apps.administracion.politica_contrasena import validar_contrasena


class SolicitarRestablecimientoSerializador(serializers.Serializer):
    """Cuerpo de la solicitud: solo el correo."""
    correo = serializers.EmailField(max_length=254)


class ConfirmarRestablecimientoSerializador(serializers.Serializer):
    """Cuerpo del restablecimiento: token + nueva contraseña."""
    token = serializers.CharField()
    contrasena = serializers.CharField(write_only=True)

    def validate_contrasena(self, valor):
        errores = validar_contrasena(valor)
        if errores:
            raise serializers.ValidationError(errores)
        return valor


class MensajeRestablecimientoSerializador(serializers.Serializer):
    """Respuesta genérica con un mensaje."""
    mensaje = serializers.CharField()