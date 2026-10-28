"""Pruebas del envío de correo por API HTTP (Brevo/Resend)."""
import json

from django.core.mail import EmailMultiAlternatives
from django.core import mail
from django.test import TestCase, override_settings
from unittest.mock import patch

from apps.email.correos import (
    correo_bienvenida,
    correo_cambio_contrasena,
    correo_inicio_sesion,
)
from apps.usuarios.modelo import Usuario

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


class CorreoBienvenidaTest(TestCase):

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='https://orbit.example',
    )
    def test_usa_ruta_de_inicio_de_sesion_y_escapa_datos_html(self):
        usuario = Usuario(
            nombre_completo='<script>alert(1)</script>',
            correo='ana&soporte@orbit.local',
        )

        correo_bienvenida(usuario)

        self.assertEqual(len(mail.outbox), 1)
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn(
            'https://orbit.example/vistas/iniciar-sesion.html',
            html,
        )
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertIn('ana&amp;soporte@orbit.local', html)
        self.assertNotIn('<script>', html)
        # El logo va como imagen remota: sin CID y sin adjuntos.
        self.assertIn('https://orbit.example/img/logo-email.png', html)
        self.assertNotIn('cid:', html)
        self.assertEqual(mail.outbox[0].attachments, [])


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    FRONTEND_URL='https://orbit.example',
)
class CorreosDeSeguridadTest(TestCase):
    """Avisos de inicio de sesión y de cambio de contraseña."""

    def setUp(self):
        self.usuario = Usuario(
            nombre_completo='Paula Paulina',
            correo='paula@orbit.local',
        )

    def test_aviso_de_inicio_de_sesion(self):
        correo_inicio_sesion(self.usuario, 'Mozilla/5.0 (Windows NT 10.0)')

        self.assertEqual(len(mail.outbox), 1)
        mensaje = mail.outbox[0]
        self.assertEqual(mensaje.to, ['paula@orbit.local'])
        self.assertIn('Inicio de sesión', mensaje.subject)
        self.assertIn('Mozilla/5.0', mensaje.alternatives[0][0])
        self.assertIn(
            'https://orbit.example/vistas/restablecer-contrasena.html',
            mensaje.alternatives[0][0],
        )

    def test_aviso_de_cambio_desde_el_perfil(self):
        correo_cambio_contrasena(self.usuario, 'perfil')

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('contraseña cambió', mail.outbox[0].subject)
        self.assertIn('perfil', mail.outbox[0].body)

    def test_aviso_de_cambio_por_restablecimiento(self):
        correo_cambio_contrasena(self.usuario, 'restablecimiento')

        self.assertIn('restableciste', mail.outbox[0].body)