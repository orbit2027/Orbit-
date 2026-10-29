from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.usuarios.modelo import Usuario
from .models import ConfiguracionAplicacion


class MantenimientoMiddleware:
    rutas_publicas_durante_mantenimiento = (
        '/api/v1/administracion/configuracion/publica/',
        '/api/v1/usuarios/login/',
        '/api/v1/restablecimiento/',
        '/api/v1/captcha/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/v1/'):
            return self.get_response(request)

        configuracion = ConfiguracionAplicacion.objects.filter(pk=1).first()
        if not configuracion or not configuracion.mantenimiento_activo:
            return self.get_response(request)
        if any(
            request.path.startswith(ruta)
            for ruta in self.rutas_publicas_durante_mantenimiento
        ):
            return self.get_response(request)
        if self._es_administrador(request):
            return self.get_response(request)

        return JsonResponse({
            'error': configuracion.mensaje_mantenimiento,
            'mantenimiento': True,
        }, status=503)

    @staticmethod
    def _es_administrador(request):
        autorizacion = request.headers.get('Authorization', '').split()
        if len(autorizacion) != 2 or autorizacion[0].lower() != 'bearer':
            return False

        try:
            token = AccessToken(autorizacion[1])
            usuario = Usuario.objects.filter(id=token['user_id']).first()
        except (TokenError, KeyError, TypeError, ValueError):
            return False

        return bool(
            usuario
            and usuario.activo
            and usuario.rol == 'administrador'
            and token.get('sv') == usuario.session_version
        )
