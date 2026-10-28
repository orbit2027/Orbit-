"""
Correos transaccionales de Orbit.
Plantilla HTML con la identidad de la marca (logo por CID) y los envíos
de bienvenida, invitación a proyecto y asignación de tarea.
"""
from html import escape
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)


def _escapar_html(valor):
    return escape(str(valor), quote=True)


def _plantilla(titulo, parrafos, boton_texto=None, boton_url=None, nota=None):
    """HTML responsive con la identidad de Orbit."""
    html_parrafos = ''.join(
        f'''<p style="margin:0 0 14px;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#94A3B8;">{parrafo}</p>'''
        for parrafo in parrafos
    )
    html_boton = ''
    if boton_texto and boton_url:
        html_boton = f'''
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
                <tr>
                  <td align="center">
                    <a href="{_escapar_html(boton_url)}"
                       style="display:inline-block;padding:14px 34px;border-radius:12px;
                              background:#00E5FF;color:#03101F;font-family:'Segoe UI',Arial,Helvetica,sans-serif;
                              font-size:16px;font-weight:700;text-decoration:none;">
                      {_escapar_html(boton_texto)}
                    </a>
                  </td>
                </tr>
              </table>'''
    html_nota = ''
    if nota:
        html_nota = f'''
              <p style="margin:0;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:13px;line-height:1.6;color:#8896A8;">
                {nota}
              </p>'''
    return f"""<!DOCTYPE html>
<html lang="es" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_escapar_html(titulo)} · Orbit</title>
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
                {_escapar_html(titulo)}
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:12px 32px;">
              {html_parrafos}
              {html_boton}
              {html_nota}
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


def enviar_correo(destinatario, asunto, html, texto_plano):
    """Envía un correo HTML con el logo incrustado por CID."""
    correo = EmailMultiAlternatives(
        subject=asunto,
        body=texto_plano,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[destinatario],
    )
    correo.attach_alternative(html, 'text/html')
    ruta_logo = settings.FRONTEND_DIR / 'img' / 'orbit-logo.png'
    if ruta_logo.exists():
        correo.attach_file(str(ruta_logo), mimetype='image/png')
    correo.send(fail_silently=True)


def _primera_palabra(usuario):
    return (usuario.nombre_completo or '').split(' ')[0] or 'usuario'


def correo_bienvenida(usuario):
    """Cuenta creada con éxito (registro o alta por un administrador)."""
    nombre = _escapar_html(_primera_palabra(usuario))
    enlace = f"{settings.FRONTEND_URL.rstrip('/')}/vistas/iniciar-sesion.html"
    html = _plantilla(
        titulo='Bienvenido a Orbit',
        parrafos=[
            f'Hola <strong style="color:#E2E8F0;">{nombre}</strong>:',
            'Tu cuenta se creó correctamente. Ya puedes organizar tus ideas '
            'en el mapa mental, planificar tus proyectos y seguir tus tareas '
            'en el tablero Kanban.',
        ],
        boton_texto='Ir a mi espacio',
        boton_url=enlace,
        nota=(
            'Inicia sesión con este correo: <strong style="color:#E2E8F0;">'
            f'{_escapar_html(usuario.correo)}</strong>'
        ),
    )
    texto = (
        f"Hola {nombre}:\n\n"
        "Tu cuenta de Orbit se creó correctamente. Ya puedes organizar tus "
        "ideas en el mapa mental, planificar tus proyectos y seguir tus tareas.\n\n"
        f"Inicia sesión en: {enlace}\n\n"
        "— Equipo de Orbit"
    )
    enviar_correo(usuario.correo, 'Bienvenido a Orbit', html, texto)


ETIQUETAS_PERMISO = {
    'ver': 'Puede ver',
    'editar': 'Puede ver y editar',
    'administrar': 'Puede administrar y compartir',
}


def enlace_invitacion(invitacion):
    """URL de la página donde se acepta o rechaza una invitación."""
    base = settings.FRONTEND_URL.rstrip('/')
    return f"{base}/vistas/invitaciones.html?invitacion={invitacion.token}"


def correo_invitacion_compartir(destinatario, propietario, invitacion, titulo):
    """
    Invitación para acceder a una tarea o proyecto.

    El acceso no se concede hasta que la persona invitada acepta el enlace.
    `destinatario` puede ser un correo sin cuenta registrada.
    """
    correo = (destinatario or '').strip()
    nombre_visible = correo.split('@')[0] or 'hola'
    nombre = _escapar_html(nombre_visible)
    tipo = 'proyecto' if invitacion.tipo_objeto == 'proyecto' else 'tarea'
    permiso = ETIQUETAS_PERMISO.get(invitacion.permiso, 'Puede ver')
    enlace = enlace_invitacion(invitacion)
    titulo_limpio = _escapar_html(titulo)
    propietario_limpio = _escapar_html(
        propietario.nombre_completo or propietario.correo
    )

    html = _plantilla(
        titulo=f'Te invitaron a un {tipo}',
        parrafos=[
            f'Hola <strong style="color:#E2E8F0;">{nombre}</strong>:',
            f'<strong style="color:#E2E8F0;">{propietario_limpio}</strong> '
            f'quiere compartir contigo el {tipo} '
            f'<strong style="color:#00E5FF;">“{titulo_limpio}”</strong> '
            f'en Orbit.',
            f'<strong style="color:#E2E8F0;">{_escapar_html(permiso)}</strong> '
            'una vez que aceptes la invitación.',
        ],
        boton_texto='Aceptar invitación',
        boton_url=enlace,
        nota=(
            'Ingresa con tu cuenta de Orbit usando este mismo correo: '
            f'<strong style="color:#E2E8F0;">{_escapar_html(correo)}</strong>. '
            'Si no esperabas esta invitación, puedes ignorar este correo.'
        ),
    )
    texto = (
        f"Hola {nombre_visible}:\n\n"
        f"{propietario.nombre_completo or propietario.correo} quiere compartir "
        f"contigo el {tipo} “{titulo}” en Orbit.\n\n"
        f"{permiso} una vez que aceptes la invitación.\n\n"
        f"Aceptar invitación: {enlace}\n\n"
        f"Ingresa con tu cuenta de Orbit usando este mismo correo: {correo}.\n\n"
        "— Equipo de Orbit"
    )
    enviar_correo(
        correo,
        f'Te invitaron al {tipo} “{titulo}” · Orbit',
        html, texto,
    )


def correo_invitacion_aceptada(propietario, invitado, tipo_objeto, titulo):
    """Avisa al dueño que la persona invitada ya aceptó la invitación."""
    tipo = 'proyecto' if tipo_objeto == 'proyecto' else 'tarea'
    nombre_invitado = _escapar_html(
        invitado.nombre_completo or invitado.correo
    )
    enlace = f"{settings.FRONTEND_URL.rstrip('/')}/vistas/tablero-kanban.html"
    html = _plantilla(
        titulo='Invitación aceptada',
        parrafos=[
            f'Hola <strong style="color:#E2E8F0;">'
            f'{_escapar_html(_primera_palabra(propietario))}</strong>:',
            f'<strong style="color:#E2E8F0;">{nombre_invitado}</strong> aceptó '
            f'tu invitación y ya tiene acceso al {tipo} '
            f'<strong style="color:#00E5FF;">“{_escapar_html(titulo)}”</strong>.',
        ],
        boton_texto='Abrir mi tablero',
        boton_url=enlace,
    )
    texto = (
        f"Hola {_primera_palabra(propietario)}:\n\n"
        f"{invitado.nombre_completo or invitado.correo} aceptó tu invitación "
        f"y ya tiene acceso al {tipo} “{titulo}”.\n\n"
        f"Abrir el tablero: {enlace}\n\n"
        "— Equipo de Orbit"
    )
    enviar_correo(
        propietario.correo,
        f'{invitado.nombre_completo or invitado.correo} aceptó tu invitación · Orbit',
        html, texto,
    )


def _fecha_legible(momento=None):
    """Fecha y hora local en formato español (dd/mm/aaaa a las hh:mm)."""
    momento = momento or timezone.localtime()
    return momento.strftime('%d/%m/%Y a las %H:%M')


def correo_inicio_sesion(usuario, navegador='', momento=None):
    """Aviso de seguridad: se inició sesión en la cuenta."""
    nombre = _escapar_html(_primera_palabra(usuario))
    cuando = _escapar_html(_fecha_legible(momento))
    detalle = _escapar_html(navegador) if navegador else 'un dispositivo no identificado'
    enlace = f"{settings.FRONTEND_URL.rstrip('/')}/vistas/restablecer-contrasena.html"
    html = _plantilla(
        titulo='Inicio de sesión en Orbit',
        parrafos=[
            f'Hola <strong style="color:#E2E8F0;">{nombre}</strong>:',
            f'Iniciaste sesión en tu cuenta el <strong style="color:#E2E8F0;">'
            f'{cuando}</strong> desde {detalle}.',
            'Si fuiste tú, no tienes que hacer nada: tu cuenta sigue segura.',
        ],
        boton_texto='Cambiar mi contraseña',
        boton_url=enlace,
        nota=(
            'Si no reconoces este acceso, cambia tu contraseña de inmediato '
            'desde el botón y revisa los movimientos de tu cuenta.'
        ),
    )
    texto = (
        f"Hola {_primera_palabra(usuario)}:\n\n"
        f"Iniciaste sesión en tu cuenta de Orbit el {_fecha_legible(momento)} "
        f"desde {navegador or 'un dispositivo no identificado'}.\n\n"
        "Si fuiste tú, no tienes que hacer nada.\n\n"
        f"Si no reconoces este acceso, cambia tu contraseña: {enlace}\n\n"
        "— Equipo de Orbit"
    )
    enviar_correo(
        usuario.correo,
        'Inicio de sesión en tu cuenta · Orbit',
        html, texto,
    )


def correo_cambio_contrasena(usuario, motivo='perfil', momento=None):
    """Aviso de que la contraseña cambió (perfil o restablecimiento)."""
    nombre = _escapar_html(_primera_palabra(usuario))
    cuando = _escapar_html(_fecha_legible(momento))
    if motivo == 'restablecimiento':
        contexto = 'restableciste tu contraseña con el enlace que enviamos por correo'
    else:
        contexto = 'cambiaste tu contraseña desde tu perfil de Orbit'
    enlace = f"{settings.FRONTEND_URL.rstrip('/')}/vistas/restablecer-contrasena.html"
    html = _plantilla(
        titulo='Tu contraseña cambió',
        parrafos=[
            f'Hola <strong style="color:#E2E8F0;">{nombre}</strong>:',
            f'El <strong style="color:#E2E8F0;">{cuando}</strong> '
            f'{_escapar_html(contexto)}.',
            'Por seguridad cerramos todas las sesiones anteriores: vuelve a '
            'iniciar sesión con tu contraseña nueva.',
        ],
        boton_texto='Iniciar sesión',
        boton_url=f"{settings.FRONTEND_URL.rstrip('/')}/vistas/iniciar-sesion.html",
        nota=(
            'Si no hiciste este cambio, restablece tu contraseña ahora: '
            f'<a href="{_escapar_html(enlace)}" style="color:#00E5FF;">'
            'recuperar mi cuenta</a>.'
        ),
    )
    texto = (
        f"Hola {_primera_palabra(usuario)}:\n\n"
        f"El {_fecha_legible(momento)} {contexto}.\n\n"
        "Por seguridad cerramos todas las sesiones anteriores.\n\n"
        f"Si no hiciste este cambio, restablece tu contraseña: {enlace}\n\n"
        "— Equipo de Orbit"
    )
    enviar_correo(
        usuario.correo,
        'Tu contraseña cambió · Orbit',
        html, texto,
    )
