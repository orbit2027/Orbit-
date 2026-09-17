"""
Pruebas del módulo de restablecimiento de contraseña.
"""
import json
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.email_api import EmailBackendAPI

from apps.usuarios.modelo import Usuario
from apps.usuarios.tokens import crear_tokens_para

from .modelo import RestablecimientoContrasena
from .vistas import generar_token, hash_token

SOLICITAR_URL = '/api/v1/restablecimiento/solicitar/'
CONFIRMAR_URL = '/api/v1/restablecimiento/confirmar/'


class BaseRestablecimientoTest(TestCase):

    def setUp(self):
        self.api = APIClient()
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        # El runner de tests fuerza DEBUG=False; desactivamos reCAPTCHA para
        # no depender del verificación externa en las pruebas.
        settings.RECAPTCHA_SECRET_KEY = ''
        self.crear_usuario('ana@orbit.local', 'Ana Perez')

    def crear_usuario(self, correo, nombre, contrasena='Prueba#123'):
        usuario = Usuario(nombre_completo=nombre, correo=correo)
        usuario.set_contrasena(contrasena)
        usuario.save()
        return usuario

    def extraer_token_del_correo(self):
        self.assertEqual(len(mail.outbox), 1)
        cuerpo = mail.outbox[0].body
        enlace = [l for l in cuerpo.splitlines() if 'token=' in l]
        self.assertTrue(enlace)
        return enlace[0].split('token=', 1)[1].strip()


class FlujoCompletoTest(BaseRestablecimientoTest):

    def test_restablece_contrasena_y_usa_el_token_una_sola_vez(self):
        respuesta = self.api.post(SOLICITAR_URL, {'correo': 'ana@orbit.local'})
        self.assertEqual(respuesta.status_code, 200)

        token = self.extraer_token_del_correo()

        respuesta = self.api.post(CONFIRMAR_URL, {
            'token': token,
            'contrasena': 'NuevaClave#99',
        })
        self.assertEqual(respuesta.status_code, 200)

        usuario = Usuario.objects.get(correo='ana@orbit.local')
        self.assertTrue(usuario.verificar_contrasena('NuevaClave#99'))
        self.assertFalse(usuario.verificar_contrasena('Prueba#123'))
        self.assertFalse(
            RestablecimientoContrasena.objects.filter(usuario=usuario).exists()
        )

        # Reutilizar el token ya no es válido
        respuesta = self.api.post(CONFIRMAR_URL, {
            'token': token,
            'contrasena': 'OtraClave#44',
        })
        self.assertEqual(respuesta.status_code, 400)

    def test_invalida_los_tokens_jwt_anteriores(self):
        usuario = Usuario.objects.get(correo='ana@orbit.local')
        token_previo = crear_tokens_para(usuario)['access']

        respuesta = self.api.post(SOLICITAR_URL, {'correo': 'ana@orbit.local'})
        self.assertEqual(respuesta.status_code, 200)
        token = self.extraer_token_del_correo()

        respuesta = self.api.post(CONFIRMAR_URL, {
            'token': token,
            'contrasena': 'NuevaClave#99',
        })
        self.assertEqual(respuesta.status_code, 200)

        # La sesión emitida antes del cambio queda revocada
        self.api.credentials(HTTP_AUTHORIZATION=f'Bearer {token_previo}')
        perfil = self.api.get('/api/v1/usuarios/perfil/')
        self.assertIn(perfil.status_code, (401, 403))

        # Un login nuevo (con la clave nueva) sí funciona
        self.api.credentials()
        login = self.api.post('/api/v1/usuarios/login/', {
            'correo': 'ana@orbit.local',
            'contrasena': 'NuevaClave#99',
        })
        self.assertEqual(login.status_code, 200)
        self.assertIn('access', login.data['tokens'])


class SolicitudSeguraTest(BaseRestablecimientoTest):

    def test_respuesta_generica_si_el_correo_no_existe(self):
        respuesta = self.api.post(SOLICITAR_URL, {'correo': 'nadie@orbit.local'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(mail.outbox, [])

    def test_respuesta_generica_si_el_correo_existe(self):
        respuesta = self.api.post(SOLICITAR_URL, {'correo': 'ana@orbit.local'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(respuesta.data['mensaje'], str(respuesta.data['mensaje']))

    def test_correo_invalido(self):
        respuesta = self.api.post(SOLICITAR_URL, {'correo': 'no-es-un-correo'})
        self.assertEqual(respuesta.status_code, 400)

    def test_requiere_correo(self):
        respuesta = self.api.post(SOLICITAR_URL, {})
        self.assertEqual(respuesta.status_code, 400)

    def test_limita_reintentos_rapidos(self):
        self.api.post(SOLICITAR_URL, {'correo': 'ana@orbit.local'})
        respuesta = self.api.post(SOLICITAR_URL, {'correo': 'ana@orbit.local'})
        self.assertEqual(respuesta.status_code, 429)

    def test_no_persiste_el_token_en_bruto(self):
        self.api.post(SOLICITAR_URL, {'correo': 'ana@orbit.local'})
        token = self.extraer_token_del_correo()
        guardado = RestablecimientoContrasena.objects.get(usuario__correo='ana@orbit.local')
        self.assertNotEqual(guardado.token_hash, token)
        self.assertEqual(guardado.token_hash, hash_token(token))
        self.assertEqual(len(token), len(generar_token()))


class ConfirmacionSeguraTest(BaseRestablecimientoTest):

    def crear_token_valido(self):
        usuario = Usuario.objects.get(correo='ana@orbit.local')
        token = generar_token()
        RestablecimientoContrasena.objects.create(
            usuario=usuario,
            token_hash=hash_token(token),
            expira_en=timezone.now() + timedelta(minutes=30),
        )
        return token

    def test_contrasena_debil_rechazada(self):
        token = self.crear_token_valido()
        respuesta = self.api.post(CONFIRMAR_URL, {
            'token': token,
            'contrasena': 'solo-minusculas',
        })
        self.assertEqual(respuesta.status_code, 400)

    def test_token_expirado_rechazado(self):
        token = self.crear_token_valido()
        RestablecimientoContrasena.objects.update(
            creado_en=timezone.now() - timedelta(hours=2)
        )
        respuesta = self.api.post(CONFIRMAR_URL, {
            'token': token,
            'contrasena': 'NuevaClave#99',
        })
        self.assertEqual(respuesta.status_code, 400)

    def test_token_inexistente_rechazado(self):
        respuesta = self.api.post(CONFIRMAR_URL, {
            'token': 'token-que-no-existe',
            'contrasena': 'NuevaClave#99',
        })
        self.assertEqual(respuesta.status_code, 400)

    def test_token_de_un_solo_uso_descarta_enlaces_previos(self):
        usuario = Usuario.objects.get(correo='ana@orbit.local')
        token_anterior = generar_token()
        RestablecimientoContrasena.objects.create(
            usuario=usuario,
            token_hash=hash_token(token_anterior),
            creado_en=timezone.now() - timedelta(minutes=10),
            expira_en=timezone.now() + timedelta(minutes=20),
        )

        respuesta = self.api.post(SOLICITAR_URL, {'correo': 'ana@orbit.local'})
        self.assertEqual(respuesta.status_code, 200)
        token_nuevo = self.extraer_token_del_correo()

        # El enlace anterior fue invalidado al solicitar uno nuevo
        respuesta = self.api.post(CONFIRMAR_URL, {
            'token': token_anterior,
            'contrasena': 'NuevaClave#99',
        })
        self.assertEqual(respuesta.status_code, 400)

        # El nuevo funciona
        respuesta = self.api.post(CONFIRMAR_URL, {
            'token': token_nuevo,
            'contrasena': 'NuevaClave#99',
        })
        self.assertEqual(respuesta.status_code, 200)


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
    @patch('apps.email_api.requests.post', return_value=_RespuestaFalsa())
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
    @patch('apps.email_api.requests.post', return_value=_RespuestaFalsa())
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