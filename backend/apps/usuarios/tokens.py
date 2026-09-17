"""
Emisión de tokens JWT con versión de sesión.
El claim `sv` permite invalidar todas las sesiones activas de un usuario
cuando cambia su contraseña (session_version) sin depender de la expiración.
"""
from rest_framework_simplejwt.tokens import RefreshToken


def crear_tokens_para(usuario):
    """Genera el par access/refresh incluyendo la versión de sesión."""
    refresh = RefreshToken.for_user(usuario)
    refresh['sv'] = usuario.session_version
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }