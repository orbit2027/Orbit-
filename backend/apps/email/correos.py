"""
Correos transaccionales de Orbit.
Plantilla HTML con la identidad de la marca (logo por CID) y los envíos
de bienvenida, invitación a proyecto y asignación de tarea.
"""
from html import escape
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

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


def correo_invitacion_proyecto(invitado, propietario, proyecto):
    """Avisan a un usuario que lo invitaron a un proyecto."""
    nombre = _escapar_html(_primera_palabra(invitado))
    enlace = f"{settings.FRONTEND_URL.rstrip('/')}/vistas/proyectos.html"
    html = _plantilla(
        titulo='Te invitaron a un proyecto',
        parrafos=[
            f'Hola <strong style="color:#E2E8F0;">{nombre}</strong>:',
            f'<strong style="color:#E2E8F0;">'
            f'{_escapar_html(propietario.nombre_completo)}</strong> '
            f'te agregó al proyecto <strong style="color:#00E5FF;">'
            f'“{_escapar_html(proyecto.nombre)}”</strong>.',
        ],
        boton_texto='Ver el proyecto',
        boton_url=enlace,
        nota='Solo las personas registradas pueden ser invitadas a un proyecto.',
    )
    texto = (
        f"Hola {nombre}:\n\n"
        f"{propietario.nombre_completo} te agregó al proyecto "
        f"“{proyecto.nombre}” de Orbit.\n\n"
        f"Ver el proyecto: {enlace}\n\n"
        "— Equipo de Orbit"
    )
    enviar_correo(
        invitado.correo,
        f'Te invitaron al proyecto “{proyecto.nombre}” · Orbit',
        html, texto,
    )


def correo_asignacion_tarea(invitado, propietario, tarea):
    """Avisan a un usuario que le asignaron una tarea."""
    nombre = _escapar_html(_primera_palabra(invitado))
    enlace = f"{settings.FRONTEND_URL.rstrip('/')}/vistas/tablero-kanban.html"
    html = _plantilla(
        titulo='Te asignaron una tarea',
        parrafos=[
            f'Hola <strong style="color:#E2E8F0;">{nombre}</strong>:',
            f'<strong style="color:#E2E8F0;">'
            f'{_escapar_html(propietario.nombre_completo)}</strong> '
            f'te asignó la tarea <strong style="color:#00E5FF;">'
            f'“{_escapar_html(tarea.titulo)}”</strong>.',
            'Puedes verla y editarla desde tu tablero.',
        ],
        boton_texto='Abrir mi tablero',
        boton_url=enlace,
    )
    texto = (
        f"Hola {nombre}:\n\n"
        f"{propietario.nombre_completo} te asignó la tarea "
        f"“{tarea.titulo}” de Orbit.\n\n"
        f"Abrir el tablero: {enlace}\n\n"
        "— Equipo de Orbit"
    )
    enviar_correo(
        invitado.correo,
        f'Nueva tarea asignada: “{tarea.titulo}” · Orbit',
        html, texto,
    )
