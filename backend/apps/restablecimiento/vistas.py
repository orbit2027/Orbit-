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
from django.core.mail import send_mail
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


def enviar_correo_restablecimiento(usuario, token):
    """Envía el correo con el enlace de restablecimiento."""
    base = settings.FRONTEND_URL.rstrip('/')
    enlace = f"{base}/vistas/restablecer-contrasena.html?token={token}"
    asunto = "Orbit - Restablecimiento de contraseña"
    cuerpo = (
        f"Hola {usuario.nombre_completo}:\n\n"
        "Recibimos una solicitud para restablecer tu contraseña. "
        "Usa el siguiente enlace (válido por 30 minutos y de un solo uso):\n\n"
        f"{enlace}\n\n"
        "Si no solicitaste este cambio, ignora este correo. Tu contraseña "
        "actual seguirá funcionando hasta que restablezcas una nueva.\n\n"
        "— Equipo de Orbit"
    )
    send_mail(
        subject=asunto,
        message=cuerpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.correo],
    )


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
