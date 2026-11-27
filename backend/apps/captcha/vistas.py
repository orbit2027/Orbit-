"""Vista que genera la imagen SVG del captcha y su sello firmado."""
from django.http import HttpResponse
from django.views.decorators.cache import never_cache

from .servicio import CABECERA_SELLO, crear_sello, generar_codigo, generar_svg


@never_cache
def vista_generar_captcha(request):
    codigo = generar_codigo()
    respuesta = HttpResponse(
        generar_svg(codigo), content_type='image/svg+xml'
    )
    # El cliente recibe el SVG y, en la cabecera, el token firmado que debe
    # devolver al enviar el formulario. No se toca la sesión: cada petición
    # genera un captcha independiente.
    respuesta[CABECERA_SELLO] = crear_sello(codigo)
    return respuesta
