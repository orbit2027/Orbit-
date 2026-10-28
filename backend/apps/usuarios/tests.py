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


class InhabilitarCuentaTest(TestCase):
    """Inhabilitar la cuenta propia (sin borrar datos)."""

    URL = '/api/v1/usuarios/inhabilitar/'
    LOGIN = '/api/v1/usuarios/login/'
    PERFIL = '/api/v1/usuarios/perfil/'
    ELIMINAR = '/api/v1/usuarios/eliminar/'

    def setUp(self):
        self.api = APIClient()
        self.usuario = self.crear('ana@orbit.local')

    def crear(self, correo, rol='usuario'):
        usuario = Usuario(nombre_completo='Ana Perez', correo=correo, rol=rol)
        usuario.set_contrasena('Prueba#123')
        usuario.save()
        return usuario

    def autenticar(self, usuario):
        tokens = crear_tokens_para(usuario)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def test_inhabilita_la_cuenta_con_la_contrasena_correcta(self):
        self.autenticar(self.usuario)

        respuesta = self.api.post(
            self.URL, {'contrasena': 'Prueba#123'}, format='json')

        self.assertEqual(respuesta.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.activo)
        # La cuenta no se borra: los datos siguen ahí
        self.assertTrue(Usuario.objects.filter(id=self.usuario.id).exists())
        # Y las sesiones anteriores quedan revocadas
        self.assertEqual(self.api.get(self.PERFIL).status_code, 403)

    def test_rechaza_la_contrasena_incorrecta(self):
        self.autenticar(self.usuario)

        respuesta = self.api.post(
            self.URL, {'contrasena': 'OtraClave#99'}, format='json')

        self.assertEqual(respuesta.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.activo)

    def test_exige_autenticacion(self):
        respuesta = self.api.post(
            self.URL, {'contrasena': 'Prueba#123'}, format='json')

        self.assertEqual(respuesta.status_code, 403)

    def test_no_permite_inhabilitar_al_unico_administrador(self):
        admin = self.crear('admin@orbit.local', rol='administrador')
        self.autenticar(admin)

        respuesta = self.api.post(
            self.URL, {'contrasena': 'Prueba#123'}, format='json')

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('único administrador', respuesta.json()['error'])
        admin.refresh_from_db()
        self.assertTrue(admin.activo)

    def test_el_admin_puede_inhabilitarse_si_hay_otro_admin(self):
        admin = self.crear('admin@orbit.local', rol='administrador')
        self.crear('admin2@orbit.local', rol='administrador')
        self.autenticar(admin)

        respuesta = self.api.post(
            self.URL, {'contrasena': 'Prueba#123'}, format='json')

        self.assertEqual(respuesta.status_code, 200)
        admin.refresh_from_db()
        self.assertFalse(admin.activo)

    def test_el_login_avisa_que_la_cuenta_esta_inhabilitada(self):
        self.usuario.activo = False
        self.usuario.save()

        respuesta = self.api.post(self.LOGIN, {
            'correo': 'ana@orbit.local', 'contrasena': 'Prueba#123',
        }, format='json')

        self.assertEqual(respuesta.status_code, 403)
        self.assertIn('inhabilitada', respuesta.json()['error'])

    def test_el_login_no_revela_la_contrasena_incorrecta(self):
        self.usuario.activo = False
        self.usuario.save()

        respuesta = self.api.post(self.LOGIN, {
            'correo': 'ana@orbit.local', 'contrasena': 'OtraClave#99',
        }, format='json')

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta.json()['error'], 'Credenciales inválidas')

    def test_no_permite_eliminar_al_unico_administrador(self):
        admin = self.crear('admin@orbit.local', rol='administrador')
        self.autenticar(admin)

        respuesta = self.api.delete(
            self.ELIMINAR, {'contrasena': 'Prueba#123'}, format='json')

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('único administrador', respuesta.json()['error'])
        self.assertTrue(Usuario.objects.filter(id=admin.id).exists())

    def test_permite_eliminar_la_cuenta_si_hay_otro_admin(self):
        admin = self.crear('admin@orbit.local', rol='administrador')
        self.crear('admin2@orbit.local', rol='administrador')
        self.autenticar(admin)

        respuesta = self.api.delete(
            self.ELIMINAR, {'contrasena': 'Prueba#123'}, format='json')

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Usuario.objects.filter(id=admin.id).exists())
