"""
Modelo Django ORM para la compartición de tareas y proyectos.
Permite invitar por correo con permisos de ver/editar/administrar.
El acceso solo se concede cuando la persona invitada acepta la invitación.
"""
import uuid

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


class Invitacion(models.Model):
    """
    Invitación pendiente para compartir una tarea o proyecto.

    Se guarda por correo (puede no tener cuenta todavía). El acceso se crea
    como `Comparticion` recién cuando la persona invitada acepta el enlace.
    """

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    propietario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='invitaciones_enviadas'
    )
    correo = models.EmailField()
    tipo_objeto = models.CharField(max_length=20, choices=TIPO_OBJETO)
    objeto_id = models.CharField(max_length=50)
    permiso = models.CharField(max_length=20, choices=PERMISOS, default='ver')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['correo', 'tipo_objeto', 'objeto_id'],
                name='unica_invitacion_por_objeto'
            )
        ]
        ordering = ['-fecha_creacion']

    def __str__(self):
        return (
            f"invitación {self.correo} -> {self.tipo_objeto} "
            f"{self.objeto_id} [{self.estado}]"
        )

    @property
    def objeto_titulo(self):
        """Título legible del elemento invitado."""
        if self.tipo_objeto == 'proyecto':
            from apps.proyectos.modelo import Proyecto
            proyecto = Proyecto.objects.filter(id=self.objeto_id).first()
            return proyecto.nombre if proyecto else 'Proyecto eliminado'
        from apps.tareas.modelo import Tarea
        tarea = Tarea.objects.filter(id=self.objeto_id).first()
        return tarea.titulo if tarea else 'Tarea eliminada'