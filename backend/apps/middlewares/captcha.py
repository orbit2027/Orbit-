"""
Middleware de verificación de reCAPTCHA v2.
Valida el token del lado del servidor antes de procesar formularios.
"""
import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

def verificar_captcha(token_captcha):
    """
    Verifica el token de reCAPTCHA con el servidor de Google.
    Retorna True si la verificación es exitosa, False en caso contrario.
    """
    if not settings.RECAPTCHA_SECRET_KEY:
        # En desarrollo sin keys configuradas, permitir peticiones
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


class VerificarCaptchaMiddleware:
    """
    Middleware que verifica reCAPTCHA en peticiones de registro y login.
    Se aplica selectivamente a las rutas que lo requieren.
    """
    # Rutas que requieren verificación de CAPTCHA
    RUTAS_CAPTCHA = [
        '/api/usuarios/registro/',
        '/api/usuarios/login/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo verificar en rutas configuradas y métodos POST
        if (
            request.method == 'POST' and
            request.path in self.RUTAS_CAPTCHA
        ):
            token = request.data.get('captcha_token', '')
            if not verificar_captcha(token):
                return Response(
                    {'error': 'Verificación CAPTCHA fallida'},
                    status=status.HTTP_403_FORBIDDEN
                )

        response = self.get_response(request)
        return response 