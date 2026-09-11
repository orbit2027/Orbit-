"""
Modelo Django ORM para tareas del tablero Kanban.
Permite crear, editar y gestionar tareas con estados y etiquetas.
"""
from django.db import models
from django.utils import timezone
from apps.usuarios.modelo import Usuario


class Tarea(models.Model):

    titulo = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=2000, default='', blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[('por_hacer', 'por_hacer'), ('en_progreso', 'en_progreso'),
                 ('completado', 'completado')],
        default='por_hacer'
    )
    etiqueta = models.CharField(max_length=50, default='', blank=True)
    color_etiqueta = models.CharField(max_length=7, default='#00E5FF', blank=True)
    fecha_limite = models.DateField(null=True, blank=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='tareas'
    )

    # ID del nodo del mapa mental si fue creado desde RF-MAP-06
    origen_nodo = models.CharField(max_length=50, default='', blank=True)

    # ID del proyecto si la tarea pertenece a un proyecto (RF-PRO-03)
    proyecto = models.CharField(max_length=50, default='', blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.titulo} [{self.estado}]"