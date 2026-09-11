"""
Rutas URL del módulo de proyectos.
Define los endpoints de CRUD y la consulta global del admin.
"""
from django.urls import path
from . import vistas

urlpatterns = [
    path('', vistas.lista_proyectos, name='lista-proyectos'),
    path('admin/todos/', vistas.proyectos_todos, name='proyectos-todos'),
    path('<str:proyecto_id>/', vistas.detalle_proyecto, name='detalle-proyecto'),
    path('<str:proyecto_id>/archivar/', vistas.archivar_proyecto, name='archivar-proyecto'),
]