"""
Vistas API para restablecer la contraseña por correo electrónico.

Diseño de seguridad:
- El token se genera con secrets.token_urlsafe (256 bits) y SOLO se guarda
  su hash SHA-256 en la base de datos.
- Expira tras RESTABLECIMIENTO_TOKEN_DURACION (30 min) y es de un solo uso.
- Respuestas genéricas para no revelar si un correo está registrado.
- Reintento limitado por usuario (RESTABLECIMIENTO_REINTENTO_SEGUNDOS).
- Al restablecer, se incrementa session_version: todas las sesiones JWT
  previas del usuario quedan invalidadas.
"""
import hashlib
import logging
import secrets

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.usuarios.modelo import Usuario

from .modelo import RestablecimientoContrasena
from .serializador import (
    ConfirmarRestablecimientoSerializador,
    SolicitarRestablecimientoSerializador,
    MensajeRestablecimientoSerializador,
)

logger = logging.getLogger(__name__)

MENSAJE_GENERICO = (
    "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña."
)
MENSAJE_ENLACE_INVALIDO = "El enlace es inválido o ya expiró."


def hash_token(token):
    """Devuelve el hash SHA-256 del token (lo único que se persiste)."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def generar_token():
    """Token aleatorio de 256 bits, que solo viaja por correo."""
    return secrets.token_urlsafe(32)


def _construir_correo_html(usuario, enlace):
    """HTML responsive con la identidad de Orbit (logo incrustado por CID)."""
    nombre = usuario.nombre_completo.split(' ')[0]
    return f"""<!DOCTYPE html>
<html lang="es" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Restablece tu contraseña · Orbit</title>
</head>
<body style="margin:0;padding:0;background:#060E1E;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#060E1E;">
    <tr>
      <td align="center" style="padding:36px 16px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
               style="max-width:560px;background:#0A192F;border:1px solid rgba(0,229,255,0.15);border-radius:16px;overflow:hidden;">
          <tr>
            <td style="padding:28px 32px 8px;background:#0A192F;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <img src="cid:orbit-logo" alt="Orbit" width="132" height="88"
                         style="display:block;border:0;outline:none;">
                    <span style="display:block;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:22px;font-weight:700;color:#E2E8F0;margin-top:6px;">
                      orbit
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px 4px;">
              <h1 style="margin:0;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:24px;font-weight:700;color:#F9FAFB;line-height:1.3;">
                Restablece tu contraseña
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:12px 32px;">
              <p style="margin:0 0 14px;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#94A3B8;">
                Hola <strong style="color:#E2E8F0;">{nombre}</strong>:
              </p>
              <p style="margin:0 0 14px;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#94A3B8;">
                Recibimos una solicitud para restablecer tu contraseña de Orbit.
                Para continuar, pulsa el botón de abajo:
              </p>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
                <tr>
                  <td align="center">
                    <a href="{enlace}"
                       style="display:inline-block;padding:14px 34px;border-radius:12px;
                              background:#00E5FF;color:#03101F;font-family:'Segoe UI',Arial,Helvetica,sans-serif;
                              font-size:16px;font-weight:700;text-decoration:none;">
                      Restablecer mi contraseña
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 14px;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:13px;line-height:1.6;color:#64748B;">
                El enlace es válido por <strong>30 minutos</strong> y solo puede usarse una vez.
                Si el botón no funciona, copia esta dirección en tu navegador:<br>
                <span style="word-break:break-all;color:#00E5FF;">{enlace}</span>
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:4px 32px 8px;">
              <p style="margin:0;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:13px;line-height:1.6;color:#8896A8;">
                Si no solicitaste este cambio, ignora este correo. Tu contraseña
                actual seguirá funcionando.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px;background:#081120;border-top:1px solid rgba(0,229,255,0.08);">
              <p style="margin:0;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:12px;color:#475569;text-align:center;">
                — Equipo de <strong style="color:#00E5FF;">Orbit</strong> · tu espacio para organizar tareas y proyectos
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def enviar_correo_restablecimiento(usuario, token):
    """Envía el correo con el enlace de restablecimiento."""
    base = settings.FRONTEND_URL.rstrip('/')
    enlace = f"{base}/vistas/restablecer-contrasena.html?token={token}"
    asunto = "Restablece tu contraseña · Orbit"
    cuerpo = (
        f"Hola {usuario.nombre_completo}:\n\n"
        "Recibimos una solicitud para restablecer tu contraseña de Orbit. "
        "Abre este enlace (válido por 30 minutos y de un solo uso):\n\n"
        f"{enlace}\n\n"
        "Si no solicitaste este cambio, ignora este correo. Tu contraseña "
        "actual seguirá funcionando.\n\n"
        "— Equipo de Orbit"
    )
    correo = EmailMultiAlternatives(
        subject=asunto,
        body=cuerpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[usuario.correo],
    )
    correo.attach_alternative(
        _construir_correo_html(usuario, enlace), 'text/html'
    )
    # Logo de Orbit incrustado (cid:orbit-logo) para que se vea en el correo.
    ruta_logo = settings.FRONTEND_DIR / 'img' / 'orbit-logo.png'
    if ruta_logo.exists():
        correo.attach_file(str(ruta_logo), mimetype='image/png')
    correo.send(fail_silently=False)


@extend_schema(
    tags=['Restablecimiento'],
    summary='Solicitar enlace de restablecimiento',
    description='Envía un correo con un token de un solo uso si el correo existe. '
                'La respuesta es genérica para no revelar cuentas registradas.',
    request=SolicitarRestablecimientoSerializador,
    responses={200: MensajeRestablecimientoSerializador, 400: None, 429: None},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def solicitar_restablecimiento(request):
    """Paso 1: pide el correo y envía el enlace por email."""
    serializador = SolicitarRestablecimientoSerializador(data=request.data)
    if not serializador.is_valid():
        return Response(
            {'error': 'Ingresa un correo electrónico válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    correo = serializador.validated_data['correo'].lower().strip()
    usuario = Usuario.objects.filter(correo=correo, activo=True).first()

    if usuario:
        limite_reintento = settings.RESTABLECIMIENTO_REINTENTO_SEGUNDOS
        reciente = RestablecimientoContrasena.objects.filter(
            usuario=usuario,
            usado=False,
        ).order_by('-creado_en').first()

        if reciente:
            segundos_desde_ultima = (
                timezone.now() - reciente.creado_en
            ).total_seconds()
            if segundos_desde_ultima < limite_reintento:
                return Response(
                    {'error': 'Ya enviamos un enlace recientemente. '
                              'Revisa tu bandeja de entrada o espera unos minutos.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        # Invalida enlaces anteriores: solo una solicitud activa por usuario.
        RestablecimientoContrasena.objects.filter(usuario=usuario).delete()

        token = generar_token()
        RestablecimientoContrasena.objects.create(
            usuario=usuario,
            token_hash=hash_token(token),
            expira_en=timezone.now() + settings.RESTABLECIMIENTO_TOKEN_DURACION,
        )
        try:
            enviar_correo_restablecimiento(usuario, token)
        except Exception:
            logger.exception("Error enviando correo de restablecimiento a %s", correo)
            return Response(
                {'error': 'No fue posible enviar el correo. Inténtalo más tarde.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return Response({'mensaje': MENSAJE_GENERICO}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Restablecimiento'],
    summary='Confirmar el restablecimiento',
    description='Valida el token de un solo uso, cambia la contraseña e '
                'invalida todas las sesiones activas del usuario.',
    request=ConfirmarRestablecimientoSerializador,
    responses={200: MensajeRestablecimientoSerializador, 400: None},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def confirmar_restablecimiento(request):
    """Paso 2: aplica la nueva contraseña si el token es válido."""
    serializador = ConfirmarRestablecimientoSerializador(data=request.data)
    if not serializador.is_valid():
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializador.validated_data['token'].strip()
    restablecimiento = (
        RestablecimientoContrasena.objects
        .filter(token_hash=hash_token(token), usado=False, usuario__activo=True)
        .select_related('usuario')
        .first()
    )
    if not restablecimiento or not restablecimiento.es_valido():
        return Response(
            {'error': MENSAJE_ENLACE_INVALIDO},
            status=status.HTTP_400_BAD_REQUEST,
        )

    usuario = restablecimiento.usuario
    usuario.set_contrasena(serializador.validated_data['contrasena'])
    # Invalida todas las sesiones JWT emitidas antes del cambio.
    usuario.session_version += 1
    usuario.save()

    # El token es de un solo uso; además limpiar enlaces del usuario.
    RestablecimientoContrasena.objects.filter(usuario=usuario).delete()

    return Response(
        {'mensaje': 'Tu contraseña fue actualizada. Ya puedes iniciar sesión.'},
        status=status.HTTP_200_OK,
    )