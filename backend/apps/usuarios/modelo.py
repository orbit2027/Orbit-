import hashlib

from django.db import models
from django.utils import timezone
import bcrypt

PREFIJO_CONTRASENA_SHA256 = 'sha256$'
LIMITE_BCRYPT_BYTES = 72


class Usuario(models.Model):

    nombre_completo = models.CharField(max_length=150)
    correo = models.EmailField(unique=True, max_length=254)
    contrasena = models.CharField(max_length=128)
    rol = models.CharField(
        max_length=20,
        choices=[('usuario', 'usuario'), ('administrador', 'administrador')],
        default='usuario'
    )
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    session_version = models.PositiveIntegerField(default=0)

    def set_contrasena(self, contrasena_plana):
        contrasena_bytes = contrasena_plana.encode('utf-8')
        salt = bcrypt.gensalt(rounds=10)
        if len(contrasena_bytes) > LIMITE_BCRYPT_BYTES:
            digest = hashlib.sha256(contrasena_bytes).hexdigest().encode('ascii')
            self.contrasena = PREFIJO_CONTRASENA_SHA256 + bcrypt.hashpw(
                digest, salt
            ).decode('utf-8')
            return

        self.contrasena = bcrypt.hashpw(contrasena_bytes, salt).decode('utf-8')

    def verificar_contrasena(self, contrasena_plana):
        contrasena_bytes = contrasena_plana.encode('utf-8')
        hash_guardado = self.contrasena
        if hash_guardado.startswith(PREFIJO_CONTRASENA_SHA256):
            contrasena_bytes = hashlib.sha256(
                contrasena_bytes
            ).hexdigest().encode('ascii')
            hash_guardado = hash_guardado[len(PREFIJO_CONTRASENA_SHA256):]

        hash_bytes = hash_guardado.encode('utf-8')
        try:
            return bcrypt.checkpw(contrasena_bytes, hash_bytes)
        except ValueError:
            if len(contrasena_bytes) > LIMITE_BCRYPT_BYTES:
                try:
                    return bcrypt.checkpw(
                        contrasena_bytes[:LIMITE_BCRYPT_BYTES],
                        hash_bytes,
                    )
                except ValueError:
                    return False
            return False

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return f"{self.nombre_completo} ({self.correo})"


def es_ultimo_administrador(usuario):
    """Indica si `usuario` es el único administrador activo del sistema.

    Se usa para impedir que la aplicación se quede sin administración: nadie
    puede inhabilitar ni eliminar a la última cuenta con rol administrador.
    """
    if usuario.rol != 'administrador' or not usuario.activo:
        return False
    return not Usuario.objects.filter(
        rol='administrador', activo=True
    ).exclude(id=usuario.id).exists()


MENSAJE_ULTIMO_ADMIN = (
    'Eres el único administrador activo. Asigna el rol de administrador a '
    'otra cuenta antes de inhabilitar o eliminar la tuya.'
)