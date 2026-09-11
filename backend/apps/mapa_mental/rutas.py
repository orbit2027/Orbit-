"""
Rutas URL del módulo de mapa mental.
Define los endpoints para nodos, conexiones y conversión a tarea.
"""
from django.urls import path
from . import vistas

urlpatterns = [
    path('', vistas.mapa_completo, name='mapa-completo'),
    path('nodos/', vistas.crear_nodo, name='crear-nodo'),
    path('nodos/<str:nodo_id>/', vistas.detalle_nodo, name='detalle-nodo'),
    path('nodos/<str:nodo_id>/convertir-tarea/',
         vistas.convertir_nodo_en_tarea, name='convertir-nodo-tarea'),
    path('conexiones/', vistas.crearConexion, name='crear-conexion'),
    path('conexiones/<str:conexion_id>/',
         vistas.eliminarConexion, name='eliminar-conexion'),
]
