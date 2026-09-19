"""Vista que genera la imagen SVG del captcha."""
from django.http import HttpResponse
from django.views.decorators.cache import never_cache

from .servicio import generar_codigo, generar_svg, guardar_en_sesion


@never_cache
def vista_generar_captcha(request):
    codigo = generar_codigo()
    guardar_en_sesion(request, codigo)
    return HttpResponse(generar_svg(codigo), content_type='image/svg+xml')