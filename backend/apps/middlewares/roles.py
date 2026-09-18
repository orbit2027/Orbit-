"""
Middleware de control de acceso por rol.
Define decoradores y funciones para restringir endpoints por tipo de usuario.
"""
from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def requerir_rol(*roles_permitidos):
    """
    Decorador que verifica si el usuario tiene uno de los roles permitidos.
    Uso: @requerir_rol('administrador')
    """
    def decorador(vista_func):
        @wraps(vista_func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'error': 'Autenticación requerida'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if request.user.rol not in roles_permitidos:
                return Response(
                    {'error': 'No tienes permisos para acceder a este recurso'},
                    status=status.HTTP_403_FORBIDDEN
                )

            return vista_func(request, *args, **kwargs)
        return wrapper
    return decorador

def verificar_propietario_o_admin(request, recurso):
    """
    Verifica si el usuario es propietario del recurso o administrador.
    Retorna True si tiene permiso, False en caso contrario.
    """
    if request.user.rol == 'administrador':
        return True
    return recurso.usuario.id == request.user.id