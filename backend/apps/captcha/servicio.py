"""
Generación y verificación del CAPTCHA SVG local de Orbit.

El código viaja firmado y con fecha dentro de un token (``django.core.signing``),
por lo que la verificación no depende de la sesión, de cookies ni de la base de
datos. Eso evita los fallos intermitentes en serverless: varias peticiones
pueden generar códigos distintos sin sobrescribirse entre sí, y un cold start
o una pestaña adicional no invalida el código que está viendo la persona.

El token se entrega en la cabecera ``X-Captcha-Sello`` junto con el SVG y se
devuelve al servidor en el campo ``captcha_sello``; la respuesta escrita va en
``captcha_codigo``. El sello caduca solo (firma con timestamp + campo ``exp``).
"""
import random
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.utils import timezone

# Alfabeto mixto (mayúsculas y minúsculas) sin caracteres ambiguos.
# Se omiten O/o, I/i, L/l y 0/1 para que las letras se lean sin confusión.
CARACTERES = (
    'ABCDEFGHJKMNPQRSTUVWXYZ'
    'abcdefghjkmnpqrstuvwxyz'
    '23456789'
)
LARGO_CODIGO = 5
ANCHO = 150
ALTO = 50

SAL_FIRMA = 'orbit.captcha.v1'
CABECERA_SELLO = 'X-Captcha-Sello'
CAMPO_SELLO = 'captcha_sello'
CAMPO_CODIGO = 'captcha_codigo'


def generar_codigo():
    azar = random.SystemRandom()
    return ''.join(azar.choice(CARACTERES) for _ in range(LARGO_CODIGO))


def generar_svg(codigo):
    """Construye el SVG del captcha en Python puro (sin Pillow)."""
    azar = random.SystemRandom()
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" height="{ALTO}" '
        f'viewBox="0 0 {ANCHO} {ALTO}">',
        f'<rect width="{ANCHO}" height="{ALTO}" rx="10" fill="#0A192F"/>',
    ]

    # Líneas de ruido.
    for _ in range(18):
        x1, y1 = azar.randint(0, ANCHO), azar.randint(0, ALTO)
        x2, y2 = azar.randint(0, ANCHO), azar.randint(0, ALTO)
        partes.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            'stroke="rgba(0,229,255,0.15)" stroke-width="1"/>'
        )

    # Puntos de ruido.
    for _ in range(28):
        cx, cy = azar.randint(0, ANCHO), azar.randint(0, ALTO)
        partes.append(
            f'<circle cx="{cx}" cy="{cy}" r="1.2" fill="rgba(226,232,240,0.28)"/>'
        )

    # Caracteres con rotación y color aleatorios.
    margen = 18
    span = (ANCHO - 2 * margen) / LARGO_CODIGO
    colores = ['#00E5FF', '#A78BFA', '#F9FAFB', '#F59E0B']
    for indice, caracter in enumerate(codigo):
        x = margen + span * indice + span / 2
        tam = azar.randint(23, 28)
        # Línea base explícita para centrar el glifo sin depender de
        # dominant-baseline (soporte irregular entre navegadores).
        y = ALTO / 2 + tam * 0.36
        rotacion = azar.randint(-28, 28)
        partes.append(
            f'<text x="{x:.1f}" y="{y:.1f}" transform="rotate({rotacion} {x:.1f} {y:.1f})" '
            f'font-family="Arial, Helvetica, sans-serif" font-weight="700" '
            f'font-size="{tam}" fill="{azar.choice(colores)}" '
            f'text-anchor="middle">{caracter}</text>'
        )

    partes.append('</svg>')
    return ''.join(partes)


def _minutos_expiracion():
    return getattr(settings, 'CAPTCHA_EXPIRACION_MINUTOS', 10)


def crear_sello(codigo):
    """Firma el código y su fecha de caducidad en un token transportable."""
    carga = {
        'codigo': str(codigo).upper(),
        'exp': int((
            timezone.now() + timedelta(minutes=_minutos_expiracion())
        ).timestamp()),
    }
    return signing.dumps(carga, salt=SAL_FIRMA)


def verificar_captcha(sello, respuesta):
    """
    Valida la firma, la caducidad y la respuesta del captcha.

    En DEBUG o con ``CAPTCHA_HABILITADO=False`` no exige verificación
    (desarrollo local y pruebas).
    """
    if settings.DEBUG or not settings.CAPTCHA_HABILITADO:
        return True

    sello = str(sello or '').strip()
    respuesta = str(respuesta or '').strip().upper()
    if not sello or not respuesta:
        return False

    try:
        carga = signing.loads(
            sello,
            salt=SAL_FIRMA,
            max_age=_minutos_expiracion() * 60,
        )
    except (signing.BadSignature, signing.SignatureExpired):
        return False

    codigo = str(carga.get('codigo', '') or '').upper()
    expiracion = carga.get('exp')
    if not codigo:
        return False
    if isinstance(expiracion, (int, float)) and expiracion < timezone.now().timestamp():
        return False
    return codigo == respuesta
