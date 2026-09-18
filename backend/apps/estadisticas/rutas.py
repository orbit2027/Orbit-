"""
Rutas URL del módulo de estadísticas.
Define el endpoint para métricas de productividad.
"""
from django.urls import path
from . import vistas

urlpatterns = [
    path('', vistas.estadisticas_usuario, name='estadisticas-usuario'),
]