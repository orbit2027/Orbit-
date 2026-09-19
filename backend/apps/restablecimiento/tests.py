"""
Pruebas del módulo de restablecimiento de contraseña.
"""
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

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
        # El runner de tests fuerza DEBUG=False; el CAPTCHA local está
        # desactivado por defecto (CAPTCHA_HABILITADO=False), así que las
        # pruebas del restablecimiento no dependen de la verificación.
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

    def test_correo_incluye_html_con_logo_y_boton(self):
        self.api.post(SOLICITAR_URL, {'correo': 'ana@orbit.local'})
        mensaje = mail.outbox[0]
        html = [
            contenido
            for contenido, mimetype in mensaje.alternatives
            if mimetype == 'text/html'
        ]
        self.assertTrue(html)
        html = html[0]
        self.assertIn('cid:orbit-logo', html)
        self.assertIn('Restablece tu contraseña', html)
        self.assertIn('Restablecer mi contraseña', html)
        self.assertIn('orbit-logo.png', [a[0] for a in mensaje.attachments])


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