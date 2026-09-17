"""
Serializadores DRF para el módulo de restablecimiento de contraseña.
"""
import re
from rest_framework import serializers


class SolicitarRestablecimientoSerializador(serializers.Serializer):
    """Cuerpo de la solicitud: solo el correo."""
    correo = serializers.EmailField(max_length=254)


class ConfirmarRestablecimientoSerializador(serializers.Serializer):
    """Cuerpo del restablecimiento: token + nueva contraseña."""
    token = serializers.CharField()
    contrasena = serializers.CharField(min_length=8, write_only=True)

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


class MensajeRestablecimientoSerializador(serializers.Serializer):
    """Respuesta genérica con un mensaje."""
    mensaje = serializers.CharField()