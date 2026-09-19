"""Pruebas del CAPTCHA SVG local."""
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .servicio import CLAVE_CODIGO

CAPTCHA_URL = '/api/v1/captcha/'
LOGIN_URL = '/api/v1/usuarios/login/'


@override_settings(CAPTCHA_HABILITADO=True, DEBUG=False)
class CaptchaLocalTest(TestCase):

    def setUp(self):
        self.api = APIClient()

    def cargar_captcha(self):
        respuesta = self.api.get(CAPTCHA_URL)
        if respuesta.status_code != 200:
            self.fail(f'No se pudo cargar el captcha: {respuesta.status_code}')
        return self.api.session.get(CLAVE_CODIGO, '')

    def _login(self, codigo=''):
        return self.api.post(LOGIN_URL, {
            'correo': 'ana@orbit.local',
            'contrasena': 'Prueba#123',
            'captcha_token': codigo,
        })

    def test_obtiene_una_imagen_svg_y_guarda_el_codigo(self):
        respuesta = self.api.get(CAPTCHA_URL)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'image/svg+xml')
        self.assertIn(b'<svg', respuesta.content)
        self.assertTrue(self.api.session.get(CLAVE_CODIGO))

    def test_rechaza_la_peticion_sin_codigo(self):
        self.cargar_captcha()
        respuesta = self._login()
        self.assertEqual(respuesta.status_code, 403)

    def test_rechaza_un_codigo_incorrecto_y_permite_reintentar(self):
        self.cargar_captcha()
        respuesta = self._login('ZZZZZ')
        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(self.api.session.get(CLAVE_CODIGO))

    def test_acepta_el_codigo_correcto_sin_distinguir_mayusculas(self):
        codigo = self.cargar_captcha()
        respuesta = self._login(codigo.lower())
        self.assertEqual(respuesta.status_code, 401)
        self.assertFalse(self.api.session.get(CLAVE_CODIGO))

    def test_el_codigo_es_de_uso_unico(self):
        codigo = self.cargar_captcha()
        self._login(codigo)
        respuesta = self._login(codigo)
        self.assertEqual(respuesta.status_code, 403)

    @override_settings(CAPTCHA_HABILITADO=False)
    def test_sin_habilitar_no_exige_captcha(self):
        self.api.get(CAPTCHA_URL)
        respuesta = self._login()
        self.assertEqual(respuesta.status_code, 401)

    @override_settings(CAPTCHA_HABILITADO=False)
    def test_deshabilitado_pasa_aunque_no_sea_debug(self):
        self.cargar_captcha()
        respuesta = self._login()
        self.assertEqual(respuesta.status_code, 401)