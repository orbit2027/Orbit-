"""
Rutas URL del módulo de usuarios.
Define los endpoints para autenticación y gestión de cuentas.
"""
from django.urls import path
from . import vistas

urlpatterns = [
    path('registro/', vistas.registrar_usuario, name='registro'),
    path('login/', vistas.iniciar_sesion, name='login'),
    path('perfil/', vistas.ver_perfil, name='perfil'),
    path('editar/', vistas.editar_perfil, name='editar-perfil'),
    path('eliminar/', vistas.eliminar_cuenta, name='eliminar-cuenta'),
    path('logout/', vistas.cerrar_sesion, name='logout'),
]
