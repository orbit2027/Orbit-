"""
Rutas del módulo de restablecimiento de contraseña.
"""
from django.urls import path
from . import vistas

urlpatterns = [
    path('solicitar/', vistas.solicitar_restablecimiento, name='restablecimiento-solicitar'),
    path('confirmar/', vistas.confirmar_restablecimiento, name='restablecimiento-confirmar'),
]