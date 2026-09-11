"""
Rutas URL del módulo de tareas.
Define los endpoints para el tablero Kanban.
"""
from django.urls import path
from . import vistas

urlpatterns = [
    path('', vistas.lista_tareas, name='lista-tareas'),
    path('<str:tarea_id>/', vistas.detalle_tarea, name='detalle-tarea'),
]
