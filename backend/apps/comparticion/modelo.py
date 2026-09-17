"""
Modelo Django ORM para la compartición de tareas y proyectos.
Permite invitar usuarios por correo con permisos de ver/editar/administrar.
"""
from django.db import models
from django.utils import timezone
from apps.usuarios.modelo import Usuario

TIPO_OBJETO = [
    ('tarea', 'tarea'),
    ('proyecto', 'proyecto'),
]

PERMISOS = [
    ('ver', 'ver'),
    ('editar', 'editar'),
    ('administrar', 'administrar'),
]


class Comparticion(models.Model):
    """Representa el acceso que un usuario tiene sobre un objeto compartido."""

    propietario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='comparticiones_creadas'
    )
    compartido_con = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='comparticiones_recibidas'
    )
    tipo_objeto = models.CharField(max_length=20, choices=TIPO_OBJETO)
    objeto_id = models.CharField(max_length=50)
    permiso = models.CharField(max_length=20, choices=PERMISOS, default='ver')
    fecha_compartida = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['compartido_con', 'tipo_objeto', 'objeto_id'],
                name='unica_comparticion_por_objeto'
            )
        ]

    def __str__(self):
        return (
            f"{self.compartido_con.correo} -> {self.tipo_objeto} "
            f"{self.objeto_id} [{self.permiso}]"
        )