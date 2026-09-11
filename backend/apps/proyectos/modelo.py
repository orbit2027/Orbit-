"""
Modelo de documento MongoEngine para proyectos del módulo de proyectos.
Permite agrupar tareas y dar contexto a la gestión diaria del usuario.
"""
from datetime import datetime
from mongoengine import Document, StringField, DateTimeField, ReferenceField
from apps.usuarios.modelo import Usuario


class Proyecto(Document):
    """
    Documento que representa un proyecto.
    Agrupa tareas y tiene identidad visual propia (color).
    """
    nombre = StringField(required=True, max_length=150)
    descripcion = StringField(max_length=500, default='')
    color = StringField(max_length=7, default='#00E5FF')
    estado = StringField(
        choices=['activo', 'archivado'],
        default='activo',
        max_length=20
    )
    fecha_limite = DateTimeField(null=True)
    usuario = ReferenceField(Usuario, required=True, reverse_delete_rule=2)
    fecha_creacion = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'proyectos',
        'indexes': ['usuario', 'estado', 'fecha_creacion']
    }

    def __str__(self):
        return f"Proyecto: {self.nombre} [{self.estado}]"