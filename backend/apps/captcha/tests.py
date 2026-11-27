"""Pruebas del CAPTCHA SVG local (sin sesión, sin cookies)."""
import json
import time as tiempo_real
from unittest import mock

from django.core import signing
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.usuarios.modelo import Usuario

from .servicio import (
    CABECERA_SELLO,
    CAMPO_CODIGO,
    CAMPO_SELLO,
    SAL_FIRMA,
    crear_sello,
)

CAPTCHA_URL = '/api/v1/captcha/'
LOGIN_URL = '/api/v1/usuarios/login/'


@override_settings(CAPTCHA_HABILITADO=True, DEBUG=False)
class CaptchaLocalTest(TestCase):

    def setUp(self):
        self.api = APIClient()
        usuario = Usuario(
            nombre_completo='Ana Perez', correo='ana@orbit.local'
        )
        usuario.set_contrasena('Prueba#123')
        usuario.save()

    def cargar_captcha(self):
        respuesta = self.api.get(CAPTCHA_URL)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'image/svg+xml')
        self.assertIn(b'<svg', respuesta.content)
        sello = respuesta[CABECERA_SELLO]
        codigo = signing.loads(sello, salt=SAL_FIRMA)['codigo']
        return sello, codigo

    def _login(self, sello='', codigo=''):
        return self.api.post(LOGIN_URL, {
            'correo': 'ana@orbit.local',
            'contrasena': 'Prueba#123',
            CAMPO_SELLO: sello,
            CAMPO_CODIGO: codigo,
        })

    def test_entrega_svg_y_sello_firmado(self):
        sello, codigo = self.cargar_captcha()
        self.assertTrue(sello)
        self.assertEqual(len(codigo), 5)
        self.assertEqual(
            signing.loads(sello, salt=SAL_FIRMA)['codigo'], codigo
        )

    def test_acepta_el_codigo_correcto(self):
        sello, codigo = self.cargar_captcha()
        respuesta = self._login(sello, codigo)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('access', respuesta.data['tokens'])

    def test_acepta_el_codigo_sin_distinguir_mayusculas(self):
        sello, codigo = '', ''
        for _ in range(10):
            sello, codigo = self.cargar_captcha()
            if any(caracter.isalpha() for caracter in codigo):
                break
        self.assertTrue(any(caracter.isalpha() for caracter in codigo))

        respuesta = self._login(sello, codigo.swapcase())
        self.assertEqual(respuesta.status_code, 200)

    def test_rechaza_un_codigo_incorrecto(self):
        sello, _ = self.cargar_captcha()
        respuesta = self._login(sello, 'ZZZZZ')
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(
            json.loads(respuesta.content)['codigo'], 'captcha_invalido'
        )

    def test_rechaza_la_peticion_sin_sello(self):
        _, codigo = self.cargar_captcha()
        respuesta = self._login('', codigo)
        self.assertEqual(respuesta.status_code, 403)

    def test_rechaza_la_peticion_sin_codigo(self):
        sello, _ = self.cargar_captcha()
        respuesta = self._login(sello, '')
        self.assertEqual(respuesta.status_code, 403)

    def test_rechaza_un_sello_manipulado(self):
        sello, codigo = self.cargar_captcha()
        manipulado = sello[:-1] + ('A' if sello[-1] != 'A' else 'B')
        respuesta = self._login(manipulado, codigo)
        self.assertEqual(respuesta.status_code, 403)

    def test_el_sello_no_depende_de_la_sesion_ni_de_la_cookie(self):
        otro_cliente = APIClient()
        captcha = otro_cliente.get(CAPTCHA_URL)
        sello = captcha[CABECERA_SELLO]
        codigo = signing.loads(sello, salt=SAL_FIRMA)['codigo']

        respuesta = self._login(sello, codigo)
        self.assertEqual(respuesta.status_code, 200)

    def test_rechaza_un_sello_expirado(self):
        momento = tiempo_real.time() - 3600
        with mock.patch('django.core.signing.time.time', return_value=momento):
            sello = crear_sello('ABC23')

        respuesta = self._login(sello, 'ABC23')
        self.assertEqual(respuesta.status_code, 403)

    def test_varios_captchas_siguen_siendo_validos_a_la_vez(self):
        primero = self.cargar_captcha()
        segundo = self.cargar_captcha()

        self.assertEqual(self._login(*segundo).status_code, 200)
        # El primero no quedó sobrescrito por el segundo.
        self.api = APIClient()
        self.assertEqual(self._login(*primero).status_code, 200)

    @override_settings(CAPTCHA_HABILITADO=False)
    def test_sin_habilitar_no_exige_captcha(self):
        respuesta = self._login()
        self.assertEqual(respuesta.status_code, 200)

    @override_settings(DEBUG=True)
    def test_en_debug_no_exige_captcha(self):
        respuesta = self._login()
        self.assertEqual(respuesta.status_code, 200)
