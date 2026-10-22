"""
Pruebas del endpoint de refresco de tokens JWT (/api/v1/usuarios/jwt/).
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.usuarios.modelo import Usuario
from apps.usuarios.tokens import crear_tokens_para

JWT_URL = '/api/v1/usuarios/jwt/'
PERFIL_URL = '/api/v1/usuarios/perfil/'


class BaseRefrescoTest(TestCase):

    def setUp(self):
        self.api = APIClient()
        self.usuario = self.crear_usuario('ana@orbit.local', 'Ana Perez')

    def crear_usuario(self, correo, nombre, contrasena='Prueba#123'):
        usuario = Usuario(nombre_completo=nombre, correo=correo)
        usuario.set_contrasena(contrasena)
        usuario.save()
        return usuario


class RefrescarJwtTest(BaseRefrescoTest):

    def test_refresca_con_refresh_valido(self):
        tokens = crear_tokens_para(self.usuario)

        respuesta = self.api.post(JWT_URL, {'refresh': tokens['refresh']})

        self.assertEqual(respuesta.status_code, 200)
        nuevos = respuesta.json()['tokens']
        self.assertIn('access', nuevos)
        self.assertIn('refresh', nuevos)
        self.assertNotEqual(nuevos['access'], tokens['access'])

    def test_el_nuevo_access_accede_al_perfil(self):
        tokens = crear_tokens_para(self.usuario)

        respuesta = self.api.post(JWT_URL, {'refresh': tokens['refresh']})
        nuevo_access = respuesta.json()['tokens']['access']

        self.api.credentials(HTTP_AUTHORIZATION=f'Bearer {nuevo_access}')
        perfil = self.api.get(PERFIL_URL)
        self.assertEqual(perfil.status_code, 200)
        self.assertEqual(perfil.json()['correo'], 'ana@orbit.local')

    def test_rechaza_texto_basura(self):
        respuesta = self.api.post(JWT_URL, {'refresh': 'no-es-un-jwt'})

        self.assertEqual(respuesta.status_code, 401)

    def test_rechaza_cuerpo_vacio(self):
        respuesta = self.api.post(JWT_URL, {})

        self.assertEqual(respuesta.status_code, 401)

    def test_rechaza_un_access_token_como_refresh(self):
        access = str(AccessToken.for_user(self.usuario))

        respuesta = self.api.post(JWT_URL, {'refresh': access})

        self.assertEqual(respuesta.status_code, 401)

    def test_rechaza_refresh_de_sesion_revocada(self):
        tokens = crear_tokens_para(self.usuario)
        # Simula un cambio de contraseña: session_version avanza
        self.usuario.set_contrasena('OtraClave#77')
        self.usuario.session_version += 1
        self.usuario.save()

        respuesta = self.api.post(JWT_URL, {'refresh': tokens['refresh']})

        self.assertEqual(respuesta.status_code, 401)
        self.assertIn('revocada', respuesta.json()['error'])

    def test_rechaza_refresh_de_usuario_desactivado(self):
        tokens = crear_tokens_para(self.usuario)
        self.usuario.activo = False
        self.usuario.save()

        respuesta = self.api.post(JWT_URL, {'refresh': tokens['refresh']})

        self.assertEqual(respuesta.status_code, 401)

    def test_refresca_con_el_token_emitido_tras_cambiar_contrasena(self):
        # Cambio de contraseña: revoca lo anterior...
        self.usuario.set_contrasena('NuevaClave#99')
        self.usuario.session_version += 1
        self.usuario.save()
        # ...pero el par emitido después del cambio trae el sv vigente
        tokens_nuevos = crear_tokens_para(self.usuario)

        respuesta = self.api.post(JWT_URL, {'refresh': tokens_nuevos['refresh']})

        self.assertEqual(respuesta.status_code, 200)

    def test_el_refresh_emitido_por_el_endpoint_tambien_funciona(self):
        tokens = crear_tokens_para(self.usuario)
        primera = self.api.post(JWT_URL, {'refresh': tokens['refresh']})
        refresh_emitido = primera.json()['tokens']['refresh']

        segunda = self.api.post(JWT_URL, {'refresh': refresh_emitido})

        self.assertEqual(segunda.status_code, 200)
        # El claim sv se conserva en la cadena de refrescos
        claim_sv = RefreshToken(segunda.json()['tokens']['refresh']).get('sv')
        self.assertEqual(claim_sv, self.usuario.session_version)
