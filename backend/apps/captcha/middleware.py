"""Middleware que exige el CAPTCHA local en las peticiones de autenticación."""
import json

from django.http import JsonResponse

from .servicio import verificar_token


def _extraer_token_captcha(request):
    """Lee captcha_token del JSON del body (o DRF request.data si existe)."""
    if hasattr(request, 'data'):
        return request.data.get('captcha_token', '')
    if request.body:
        try:
            return json.loads(request.body).get('captcha_token', '')
        except (ValueError, TypeError):
            pass
    return request.POST.get('captcha_token', '')


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
            token = _extraer_token_captcha(request)
            if not verificar_token(request, token):
                return JsonResponse(
                    {'error': 'Verificación CAPTCHA fallida'},
                    status=403,
                )
        return self.get_response(request)