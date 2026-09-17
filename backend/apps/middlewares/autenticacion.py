"""
Middleware de autenticación JWT.
Verifica la validez del token en peticiones protegidas.
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from apps.usuarios.modelo import Usuario


class EsquemaAutenticacionJWT(OpenApiAuthenticationExtension):
    """Describe el esquema Bearer JWT en la documentación OpenAPI."""
    target_class = 'apps.middlewares.autenticacion.AutenticacionJWT'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }


class AutenticacionJWT(BaseAuthentication):
    """
    Clase de autenticación personalizada que verifica JWT.
    Se integra con el sistema de autenticación de DRF.
    """
    def authenticate(self, request):
        # Obtener el header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            # Decodificar y validar el token
            token_acceso = AccessToken(token)
            usuario_id = token_acceso['user_id']

            # Buscar el usuario en la base de datos
            usuario = Usuario.objects.filter(id=usuario_id, activo=True).first()
            if not usuario:
                raise AuthenticationFailed("Usuario no encontrado o desactivado.")

            return (usuario, token)
        except Exception as e:
            raise AuthenticationFailed("Token inválido o expirado.")