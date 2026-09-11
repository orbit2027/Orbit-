"""
Modelos de documentos MongoEngine para el mapa mental interactivo.
Define nodos, conexiones y su relación con el módulo de tareas.
"""
from datetime import datetime
from mongoengine import (
    Document, StringField, FloatField,
    BooleanField, DateTimeField, ReferenceField
)
from apps.usuarios.modelo import Usuario


class NodoMapa(Document):
    """
    Documento que representa un nodo visual en el mapa mental.
    Puede convertirse en tarea del tablero Kanban (RF-MAP-06).
    """
    texto = StringField(required=True, max_length=200)
    color = StringField(max_length=7, default='#00E5FF')
    posicion_x = FloatField(default=0.0)
    posicion_y = FloatField(default=0.0)
    usuario = ReferenceField(Usuario, required=True, reverse_delete_rule=2)

    # Control de conversión a tarea
    convertido_en_tarea = BooleanField(default=False)
    id_tarea_generada = StringField(max_length=50, default='')
    fecha_creacion = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'nodos_mapa',
        'indexes': ['usuario', 'convertido_en_tarea']
    }

    def __str__(self):
        return f"Nodo: {self.texto} (color: {self.color})"


class ConexionNodo(Document):
    """
    Documento que representa una conexión visual entre dos nodos.
    Las conexiones se eliminan automáticamente si se elimina alguno de los nodos.
    """
    nodo_origen = ReferenceField(
        NodoMapa, required=True, reverse_delete_rule=2
    )
    nodo_destino = ReferenceField(
        NodoMapa, required=True, reverse_delete_rule=2
    )
    usuario = ReferenceField(Usuario, required=True, reverse_delete_rule=2)

    meta = {
        'collection': 'conexiones_nodo',
        'indexes': ['usuario', 'nodo_origen', 'nodo_destino']
    }

    def __str__(self):
        return f"Conexión: {self.nodo_origen.texto} → {self.nodo_destino.texto}"