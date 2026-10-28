"""Pruebas de la gestión de usuarios del panel de administración."""
from django.test import TestCase
from rest_framework.test import APIClient

from apps.usuarios.modelo import Usuario
from apps.usuarios.tokens import crear_tokens_para

TOGGLE = '/api/v1/administracion/usuarios/{}/toggle/'
PERFIL = '/api/v1/usuarios/perfil/'
LOGIN = '/api/v1/usuarios/login/'


class BaseAdminTest(TestCase):

    def setUp(self):
        self.api = APIClient()
        self.admin = self.crear('admin@orbit.local', rol='administrador',
                                nombre='Admin Orbit')

    def crear(self, correo, rol='usuario', nombre='Usuario Prueba',
              contrasena='Prueba#123', activo=True):
        usuario = Usuario(
            nombre_completo=nombre,
            correo=correo,
            rol=rol,
            activo=activo,
        )
        usuario.set_contrasena(contrasena)
        usuario.save()
        return usuario

    def autenticar(self, usuario):
        tokens = crear_tokens_para(usuario)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        return tokens


class ToggleUsuarioTest(BaseAdminTest):

    def test_el_admin_puede_desactivar_a_un_usuario_normal(self):
        self.autenticar(self.admin)
        usuario = self.crear('ana@orbit.local')

        respuesta = self.api.patch(TOGGLE.format(usuario.id))

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()['activo'])
        usuario.refresh_from_db()
        self.assertFalse(usuario.activo)

    def test_desactivar_invalida_las_sesiones_del_usuario(self):
        usuario = self.crear('ana@orbit.local')
        tokens_usuario = crear_tokens_para(usuario)

        self.autenticar(self.admin)
        self.api.patch(TOGGLE.format(usuario.id))

        # El token emitido antes de la desactivación ya no sirve
        self.api.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens_usuario['access']}")
        perfil = self.api.get(PERFIL)

        self.assertEqual(perfil.status_code, 403)

    def test_reactivar_permite_entrar_de_nuevo(self):
        self.autenticar(self.admin)
        usuario = self.crear('ana@orbit.local', activo=False)

        respuesta = self.api.patch(TOGGLE.format(usuario.id))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()['activo'])

        self.api.credentials()
        login = self.api.post(LOGIN, {
            'correo': 'ana@orbit.local', 'contrasena': 'Prueba#123',
        }, format='json')
        self.assertEqual(login.status_code, 200)

    def test_no_permite_desactivar_al_unico_administrador(self):
        self.autenticar(self.admin)

        respuesta = self.api.patch(TOGGLE.format(self.admin.id))

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('único administrador', respuesta.json()['error'])
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)

    def test_permite_desactivar_a_un_admin_si_hay_otro_activo(self):
        self.autenticar(self.admin)
        otro = self.crear('admin2@orbit.local', rol='administrador')

        respuesta = self.api.patch(TOGGLE.format(otro.id))

        self.assertEqual(respuesta.status_code, 200)
        otro.refresh_from_db()
        self.assertFalse(otro.activo)
        # El admin que hizo la petición sigue activo y con sesión válida
        self.assertEqual(self.api.get(PERFIL).status_code, 200)

    def test_el_admin_puede_desactivarse_si_hay_otro_admin(self):
        self.autenticar(self.admin)
        self.crear('admin2@orbit.local', rol='administrador')

        respuesta = self.api.patch(TOGGLE.format(self.admin.id))

        self.assertEqual(respuesta.status_code, 200)
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.activo)

    def test_un_usuario_normal_no_puede_usar_el_endpoint(self):
        usuario = self.crear('ana@orbit.local')
        self.autenticar(usuario)

        respuesta = self.api.patch(TOGGLE.format(self.admin.id))

        self.assertEqual(respuesta.status_code, 403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)
