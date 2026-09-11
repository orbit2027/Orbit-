"""
Modelo de documento MongoEngine para tareas del tablero Kanban.
Permite crear, editar y gestionar tareas con estados y etiquetas.
"""
from datetime import datetime
from mongoengine import (
    Document, StringField, DateTimeField,
    ReferenceField
)
from apps.usuarios.modelo import Usuario

class Tarea(Document):

    titulo = StringField(required=True, max_length=200)
    descripcion = StringField(max_length=2000, default='')
    estado = StringField(
        required=True,
        choices=['por_hacer', 'en_progreso', 'completado'],
        default='por_hacer',
        max_length=20
    )
    etiqueta = StringField(max_length=50, default='')
    color_etiqueta = StringField(max_length=7, default='#00E5FF')
    fecha_limite = DateTimeField(null=True)
    usuario = ReferenceField(Usuario, required=True, reverse_delete_rule=2)

    # ID del nodo del mapa mental si fue creado desde RF-MAP-06
    origen_nodo = StringField(max_length=50, default='')

    # ID del proyecto si la tarea pertenece a un proyecto (RF-PRO-03)
    proyecto = StringField(max_length=50, default='')
    fecha_creacion = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'tareas',
        'indexes': ['usuario', 'estado', 'fecha_creacion']
    }

    def __str__(self):
        return f"{self.titulo} [{self.estado}]"