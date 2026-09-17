from django.db import models
from django.utils import timezone
import bcrypt

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
        salt = bcrypt.gensalt(rounds=10)
        self.contrasena = bcrypt.hashpw(
            contrasena_plana.encode('utf-8'), salt
        ).decode('utf-8')

    def verificar_contrasena(self, contrasena_plana):
        return bcrypt.checkpw(
            contrasena_plana.encode('utf-8'),
            self.contrasena.encode('utf-8')
        )

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return f"{self.nombre_completo} ({self.correo})"