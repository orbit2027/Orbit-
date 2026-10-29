"""Pruebas de la gestión de usuarios del panel de administración."""
import json
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from apps.usuarios.modelo import Usuario
from apps.usuarios.tokens import crear_tokens_para
from apps.tareas.modelo import Tarea
from apps.proyectos.modelo import Proyecto
from apps.usuarios.serializador import RegistroUsuarioSerializador
from .models import obtener_configuracion
from .middleware import MantenimientoMiddleware

TOGGLE = '/api/v1/administracion/usuarios/{}/toggle/'
PERFIL = '/api/v1/usuarios/perfil/'
LOGIN = '/api/v1/usuarios/login/'
ADMIN_STATS = '/api/v1/administracion/estadisticas/'
ADMIN_CONFIG = '/api/v1/administracion/configuracion/'
PUBLIC_CONFIG = '/api/v1/administracion/configuracion/publica/'
ADMIN_TASKS = '/api/v1/administracion/contenido/tareas/'
ADMIN_PROJECTS = '/api/v1/administracion/contenido/proyectos/'
ADMIN_CREATE_USER = '/api/v1/administracion/usuarios/crear/'


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


class AdministracionAvanzadaTest(BaseAdminTest):

    @patch('apps.administracion.vistas.correo_bienvenida')
    def test_admin_puede_crear_otro_administrador_desde_el_panel(self, _correo):
        self.autenticar(self.admin)

        respuesta = self.api.post(ADMIN_CREATE_USER, {
            'nombre_completo': 'Nueva Administradora',
            'correo': 'nueva-admin@orbit.local',
            'contrasena': 'Prueba#123',
            'rol': 'administrador',
        }, format='json')

        self.assertEqual(respuesta.status_code, 201, respuesta.content)
        self.assertEqual(respuesta.json()['rol'], 'administrador')
        creada = Usuario.objects.get(correo='nueva-admin@orbit.local')
        self.assertEqual(creada.rol, 'administrador')

    def test_politica_de_contrasena_configurable_se_aplica_al_registro(self):
        configuracion = obtener_configuracion()
        configuracion.longitud_minima_contrasena = 12
        configuracion.exigir_mayuscula = False
        configuracion.exigir_numero = True
        configuracion.save()

        serializador = RegistroUsuarioSerializador(data={
            'nombre_completo': 'Usuario Nuevo',
            'correo': 'nuevo@orbit.local',
            'contrasena': 'abcdefghi123',
        })

        self.assertTrue(serializador.is_valid(), serializador.errors)

        serializador = RegistroUsuarioSerializador(data={
            'nombre_completo': 'Usuario Nuevo',
            'correo': 'nuevo@orbit.local',
            'contrasena': 'abcdefghij1',
        })
        self.assertFalse(serializador.is_valid())

    def test_informe_incluye_metricas_de_proyectos(self):
        Proyecto.objects.create(nombre='Proyecto de prueba', usuario=self.admin)
        self.autenticar(self.admin)

        respuesta = self.api.get(ADMIN_STATS)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['proyectos_totales'], 1)
        self.assertEqual(respuesta.json()['proyectos_activos'], 1)
        self.assertEqual(respuesta.json()['usuarios_activos'], 1)

    def test_admin_puede_editar_y_eliminar_tareas_globales(self):
        tarea = Tarea.objects.create(
            titulo='Tarea original',
            usuario=self.admin,
        )
        self.autenticar(self.admin)

        respuesta = self.api.get(ADMIN_TASKS)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()[0]['propietario'], self.admin.nombre_completo)

        respuesta = self.api.patch(
            f'{ADMIN_TASKS}{tarea.id}/',
            {'titulo': 'Tarea moderada', 'estado': 'completado'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, 200)
        tarea.refresh_from_db()
        self.assertEqual(tarea.titulo, 'Tarea moderada')

        respuesta = self.api.delete(f'{ADMIN_TASKS}{tarea.id}/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Tarea.objects.filter(id=tarea.id).exists())

    def test_admin_puede_editar_proyectos_y_borrarlos_sin_borrar_tareas(self):
        proyecto = Proyecto.objects.create(nombre='Proyecto original', usuario=self.admin)
        tarea = Tarea.objects.create(
            titulo='Tarea preservada',
            usuario=self.admin,
            proyecto=str(proyecto.id),
        )
        self.autenticar(self.admin)

        respuesta = self.api.patch(
            f'{ADMIN_PROJECTS}{proyecto.id}/',
            {'nombre': 'Proyecto moderado', 'estado': 'archivado'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, 200)
        proyecto.refresh_from_db()
        self.assertEqual(proyecto.nombre, 'Proyecto moderado')

        respuesta = self.api.delete(f'{ADMIN_PROJECTS}{proyecto.id}/')
        self.assertEqual(respuesta.status_code, 200)
        tarea.refresh_from_db()
        self.assertEqual(tarea.proyecto, '')

    def test_usuario_normal_no_puede_moderar_contenido(self):
        usuario = self.crear('ana@orbit.local')
        self.autenticar(usuario)

        self.assertEqual(self.api.get(ADMIN_TASKS).status_code, 403)
        self.assertEqual(self.api.get(ADMIN_PROJECTS).status_code, 403)
        self.assertEqual(self.api.get(ADMIN_CONFIG).status_code, 403)

    def test_admin_actualiza_configuracion_publica_y_politica(self):
        self.autenticar(self.admin)
        datos = {
            'aviso_global': 'Actualización programada',
            'mantenimiento_activo': False,
            'mensaje_mantenimiento': 'Volvemos pronto',
            'longitud_minima_contrasena': 12,
            'exigir_mayuscula': False,
            'exigir_numero': True,
        }

        respuesta = self.api.put(ADMIN_CONFIG, datos, format='json')
        self.assertEqual(respuesta.status_code, 200)
        respuesta_publica = self.api.get(PUBLIC_CONFIG)

        self.assertEqual(respuesta_publica.status_code, 200)
        self.assertEqual(respuesta_publica.json()['aviso_global'], 'Actualización programada')
        self.assertEqual(
            respuesta_publica.json()['politica_contrasena'],
            {
                'longitud_minima': 12,
                'mayuscula_requerida': False,
                'numero_requerido': True,
            },
        )

    def test_mantenimiento_bloquea_usuarios_y_permite_administradores(self):
        usuario = self.crear('ana@orbit.local')
        configuracion = obtener_configuracion()
        configuracion.mantenimiento_activo = True
        configuracion.mensaje_mantenimiento = 'Estamos actualizando.'
        configuracion.save()

        middleware = MantenimientoMiddleware(
            lambda request: HttpResponse(status=200)
        )
        token_usuario = crear_tokens_para(usuario)['access']
        solicitud_usuario = RequestFactory().get(
            '/api/v1/tareas/',
            HTTP_AUTHORIZATION=f'Bearer {token_usuario}',
        )
        respuesta_usuario = middleware(solicitud_usuario)
        self.assertEqual(respuesta_usuario.status_code, 503)
        self.assertTrue(json.loads(respuesta_usuario.content)['mantenimiento'])

        respuesta_publica = self.api.get(PUBLIC_CONFIG)
        self.assertEqual(respuesta_publica.status_code, 200)

        token_admin = crear_tokens_para(self.admin)['access']
        solicitud_admin = RequestFactory().get(
            '/api/v1/administracion/estadisticas/',
            HTTP_AUTHORIZATION=f'Bearer {token_admin}',
        )
        self.assertEqual(middleware(solicitud_admin).status_code, 200)

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
