"""
Generación y verificación del CAPTCHA SVG local de Orbit.

No depende de servicios externos (Google reCAPTCHA retirado). El servidor
genera una imagen SVG con un código aleatorio de 5 caracteres, lo guarda en la
sesión y la verificación consume el código (uso único, con expiración).
"""
import random
from datetime import datetime, timedelta

from django.conf import settings

# Alfabeto sin caracteres ambiguos (0/O/1/I/L se omiten).
CARACTERES = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
LARGO_CODIGO = 5
ANCHO = 150
ALTO = 50

CLAVE_CODIGO = 'captcha_codigo'
CLAVE_HORA = 'captcha_hora'


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
        y = ALTO / 2 + 3
        rotacion = azar.randint(-28, 28)
        partes.append(
            f'<text x="{x:.1f}" y="{y:.1f}" transform="rotate({rotacion} {x:.1f} {y:.1f})" '
            f'font-family="Arial, Helvetica, sans-serif" font-weight="700" '
            f'font-size="{azar.randint(23, 28)}" fill="{azar.choice(colores)}" '
            f'text-anchor="middle" dominant-baseline="middle">{caracter}</text>'
        )

    partes.append('</svg>')
    return ''.join(partes)


def guardar_en_sesion(request, codigo):
    request.session[CLAVE_CODIGO] = codigo
    request.session[CLAVE_HORA] = datetime.now().isoformat()


def _esta_expirado(request):
    hora = request.session.get(CLAVE_HORA, '')
    if not hora:
        return True
    try:
        creado = datetime.fromisoformat(hora)
        minutos = getattr(settings, 'CAPTCHA_EXPIRACION_MINUTOS', 10)
        return datetime.now() - creado > timedelta(minutes=minutos)
    except (TypeError, ValueError):
        return True


def verificar_token(request, token_captcha):
    """
    Valida el código enviado contra el guardado en sesión.

    Consume el código al acertar (uso único). En DEBUG o sin habilitar el
    captcha no exige verificación (dev local y pruebas).
    """
    if settings.DEBUG or not settings.CAPTCHA_HABILITADO:
        return True

    codigo = str(request.session.get(CLAVE_CODIGO, '') or '').upper()
    if not codigo or _esta_expirado(request):
        return False

    enviado = str(token_captcha or '').upper().strip()
    if codigo != enviado:
        return False

    request.session.pop(CLAVE_CODIGO, None)
    request.session.pop(CLAVE_HORA, None)
    return True