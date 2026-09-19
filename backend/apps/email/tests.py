"""Pruebas del envío de correo por API HTTP (Brevo/Resend)."""
import json

from django.core.mail import EmailMultiAlternatives
from django.test import TestCase, override_settings
from unittest.mock import patch

from .backend import EmailBackendAPI


class _RespuestaFalsa:
    status_code = 201
    text = 'ok'


class CorreoApiHttpTest(TestCase):
    """Envío por API HTTP (gratuito, sin SMTP)."""

    def _mensaje(self):
        correo = EmailMultiAlternatives(
            subject='Asunto de prueba',
            body='Cuerpo de texto',
            from_email='Orbit <remitente@orbit.local>',
            to=['destino@orbit.local'],
        )
        correo.attach_alternative('<p>Cuerpo HTML</p>', 'text/html')
        return correo

    @override_settings(EMAIL_API_PROVIDER='brevo', EMAIL_API_KEY='clave-prueba')
    @patch('apps.email.backend.requests.post', return_value=_RespuestaFalsa())
    def test_envia_a_brevo_con_el_payload_correcto(self, post):
        enviados = EmailBackendAPI().send_messages([self._mensaje()])
        self.assertEqual(enviados, 1)

        url = post.call_args[0][0]
        payload = json.loads(post.call_args.kwargs['data'])
        self.assertEqual(url, 'https://api.brevo.com/v3/smtp/email')
        self.assertEqual(payload['sender']['email'], 'remitente@orbit.local')
        self.assertEqual(payload['sender']['name'], 'Orbit')
        self.assertEqual(payload['to'], [{'email': 'destino@orbit.local'}])
        self.assertEqual(payload['textContent'], 'Cuerpo de texto')
        self.assertEqual(payload['htmlContent'], '<p>Cuerpo HTML</p>')

    @override_settings(EMAIL_API_PROVIDER='resend', EMAIL_API_KEY='clave-prueba')
    @patch('apps.email.backend.requests.post', return_value=_RespuestaFalsa())
    def test_envia_a_resend_con_el_payload_correcto(self, post):
        enviados = EmailBackendAPI().send_messages([self._mensaje()])
        self.assertEqual(enviados, 1)

        url = post.call_args[0][0]
        payload = json.loads(post.call_args.kwargs['data'])
        self.assertEqual(url, 'https://api.resend.com/emails')
        self.assertEqual(payload['to'], ['destino@orbit.local'])
        self.assertEqual(payload['html'], '<p>Cuerpo HTML</p>')

    @override_settings(EMAIL_API_PROVIDER='brevo', EMAIL_API_KEY='')
    def test_falla_sin_api_key(self):
        with self.assertRaises(ValueError):
            EmailBackendAPI().send_messages([self._mensaje()])

    def test_parsea_nombre_y_correo_del_remitente(self):
        self.assertEqual(
            EmailBackendAPI._parsear_remitente('Orbit <a@b.com>'),
            ('Orbit', 'a@b.com'),
        )
        self.assertEqual(
            EmailBackendAPI._parsear_remitente('a@b.com'),
            (None, 'a@b.com'),
        )