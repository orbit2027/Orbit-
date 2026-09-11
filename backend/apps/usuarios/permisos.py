from rest_framework.permissions import BasePermission


class EsAdministrador(BasePermission):

    message = "No tienes permisos para acceder a este recurso."
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.rol == 'administrador'
        )

class EsPropietario(BasePermission):
    """
    Permiso que permite acceso solo al propietario del recurso.
    Se usa en endpoints de perfil y gestión de cuenta propia.
    """
    message = "No tienes permisos para acceder a este recurso."

    def has_object_permission(self, request, view, obj):
        return obj.usuario.id == request.user.id


class EsAdministradorOPropietario(BasePermission):
    """
    Permiso combinado: permite a administradores o al propietario.
    """
    message = "No tienes permisos para acceder a este recurso."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.rol == 'administrador':
            return True
        return obj.usuario.id == request.user.id