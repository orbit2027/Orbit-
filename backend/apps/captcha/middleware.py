"""Middleware que exige el CAPTCHA local en las peticiones de autenticación."""
import json

from django.http import JsonResponse

from .servicio import CAMPO_CODIGO, CAMPO_SELLO, verificar_captcha


def _leer_campos(request):
    """Lee `captcha_sello` y `captcha_codigo` del JSON del body (o DRF)."""
    datos = None
    if hasattr(request, 'data') and hasattr(request.data, 'get'):
        datos = request.data
    elif request.body:
        try:
            datos = json.loads(request.body)
        except (ValueError, TypeError):
            datos = None
    if datos is None and request.POST:
        datos = request.POST
    if not hasattr(datos, 'get'):
        return '', ''
    return (
        str(datos.get(CAMPO_SELLO, '') or ''),
        str(datos.get(CAMPO_CODIGO, '') or ''),
    )


class VerificarCaptchaMiddleware:
    """Verifica el CAPTCHA en registro, login y restablecimiento de contraseña."""

    RUTAS_CAPTCHA = [
        '/api/v1/usuarios/registro/',
        '/api/v1/usuarios/login/',
        '/api/v1/restablecimiento/solicitar/',
        '/api/v1/restablecimiento/confirmar/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and request.path in self.RUTAS_CAPTCHA:
            sello, codigo = _leer_campos(request)
            if not verificar_captcha(sello, codigo):
                return JsonResponse(
                    {
                        'error': 'Verificación CAPTCHA fallida',
                        'codigo': 'captcha_invalido',
                    },
                    status=403,
                )
        return self.get_response(request)
