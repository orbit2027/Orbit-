"""
Middleware de verificación de reCAPTCHA v2.
Valida el token del lado del servidor antes de procesar formularios.
"""
import json
import requests
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status


def verificar_captcha(token_captcha):
    """
    Verifica el token de reCAPTCHA con el servidor de Google.
    Retorna True si la verificación es exitosa, False en caso contrario.
    """
    if not settings.RECAPTCHA_SECRET_KEY:
        # En desarrollo sin keys configuradas, permitir peticiones
        return True

    # En desarrollo local el frontend omite el captcha (mismo criterio usado
    # en el cliente); en producción (DEBUG=False) siempre se exige.
    if settings.DEBUG:
        return True

    url_verificacion = 'https://www.google.com/recaptcha/api/siteverify'
    datos = {
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': token_captcha
    }

    try:
        respuesta = requests.post(url_verificacion, data=datos, timeout=5)
        resultado = respuesta.json()
        return resultado.get('success', False)
    except requests.RequestException:
        # Si falla la conexión con Google, permitir en desarrollo
        if settings.DEBUG:
            return True
        return False


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
    """
    Middleware que verifica reCAPTCHA en peticiones de registro, login y
    restablecimiento de contraseña.
    Se aplica selectivamente a las rutas que lo requieren.
    """
    # Rutas que requieren verificación de CAPTCHA
    RUTAS_CAPTCHA = [
        '/api/v1/usuarios/registro/',
        '/api/v1/usuarios/login/',
        '/api/v1/restablecimiento/solicitar/',
        '/api/v1/restablecimiento/confirmar/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo verificar en rutas configuradas y métodos POST
        if (
            request.method == 'POST' and
            request.path in self.RUTAS_CAPTCHA
        ):
            token = _extraer_token_captcha(request)
            if not verificar_captcha(token):
                return JsonResponse(
                    {'error': 'Verificación CAPTCHA fallida'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        response = self.get_response(request)
        return response