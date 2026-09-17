"""
Backend de correo por API HTTP (gratuito).

Se usa cuando el host bloquea las conexiones SMTP salientes (por ejemplo, las
cuentas gratuitas de PythonAnywhere solo permiten HTTP/HTTPS). Evita SMTP por
completo: envía con una petición HTTPS a la API del proveedor.

Activación en .env:
    EMAIL_BACKEND=apps.email_api.EmailBackendAPI
    EMAIL_API_PROVIDER=brevo          # o resend
    EMAIL_API_KEY=xxxxx

Proveedores soportados:
    - brevo:  POST https://api.brevo.com/v3/smtp/email   (300 correos/día gratis)
    - resend: POST https://api.resend.com/emails         (3.000/mes gratis)
"""
import json

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class EmailBackendAPI(BaseEmailBackend):
    """Envío de correo mediante API HTTP en lugar de SMTP."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        enviados = 0
        for mensaje in email_messages:
            try:
                self._enviar(mensaje)
                enviados += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return enviados

    def _enviar(self, mensaje):
        proveedor = getattr(settings, 'EMAIL_API_PROVIDER', 'brevo').lower()
        api_key = getattr(settings, 'EMAIL_API_KEY', '')
        if not api_key:
            raise ValueError('EMAIL_API_KEY no está configurada.')

        remitente = mensaje.from_email or settings.DEFAULT_FROM_EMAIL
        nombre, correo = self._parsear_remitente(remitente)

        html = None
        for contenido, mimetype in getattr(mensaje, 'alternatives', []):
            if mimetype == 'text/html':
                html = contenido
                break

        if proveedor == 'resend':
            url = 'https://api.resend.com/emails'
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            }
            payload = {
                'from': remitente,
                'to': mensaje.to,
                'subject': mensaje.subject,
                'text': mensaje.body,
            }
            if html:
                payload['html'] = html
        else:  # brevo (por defecto)
            url = 'https://api.brevo.com/v3/smtp/email'
            headers = {
                'api-key': api_key,
                'Content-Type': 'application/json',
            }
            remitente_payload = {'email': correo}
            if nombre:
                remitente_payload['name'] = nombre
            payload = {
                'sender': remitente_payload,
                'to': [{'email': destino} for destino in mensaje.to],
                'subject': mensaje.subject,
                'textContent': mensaje.body,
            }
            if html:
                payload['htmlContent'] = html

        respuesta = requests.post(
            url, headers=headers, data=json.dumps(payload), timeout=10
        )
        if respuesta.status_code >= 300:
            raise RuntimeError(
                f"Proveedor {proveedor} respondió {respuesta.status_code}: "
                f"{respuesta.text[:200]}"
            )
        return True

    @staticmethod
    def _parsear_remitente(remitente):
        """'Nombre <correo@x>' -> ('Nombre', 'correo@x')."""
        if '<' in remitente and '>' in remitente:
            nombre = remitente.split('<')[0].strip().strip('"')
            correo = remitente.split('<')[1].split('>')[0].strip()
            return (nombre or None), correo
        return None, remitente