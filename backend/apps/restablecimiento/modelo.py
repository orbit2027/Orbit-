"""
Modelo de tokens de restablecimiento de contraseña.
Solo se almacena el hash SHA-256 del token; el valor real solo viaja en el
correo enviado al usuario, de modo que una filtración de la base de datos
no permite restablecer contraseñas.
"""
from django.db import models
from django.utils import timezone
from apps.usuarios.modelo import Usuario


class RestablecimientoContrasena(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='restablecimientos',
    )
    token_hash = models.CharField(max_length=64, unique=True)
    creado_en = models.DateTimeField(default=timezone.now)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)

    def es_valido(self):
        from django.conf import settings
        if self.usado:
            return False
        limite = self.creado_en + settings.RESTABLECIMIENTO_TOKEN_DURACION
        return timezone.now() <= limite

    def __str__(self):
        return f"Restablecimiento para {self.usuario.correo}"