"""
Modelo Django ORM para proyectos del módulo de proyectos.
Permite agrupar tareas y dar contexto a la gestión diaria del usuario.
"""
from django.db import models
from django.utils import timezone
from apps.usuarios.modelo import Usuario


class Proyecto(models.Model):
    """
    Modelo que representa un proyecto.
    Agrupa tareas y tiene identidad visual propia (color).
    """
    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=500, default='', blank=True)
    color = models.CharField(max_length=7, default='#00E5FF', blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[('activo', 'activo'), ('archivado', 'archivado')],
        default='activo'
    )
    fecha_limite = models.DateField(null=True, blank=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='proyectos'
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Proyecto: {self.nombre} [{self.estado}]"