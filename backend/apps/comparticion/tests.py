"""
Pruebas del módulo de compartición: permisos, validación de cuentas
y correos de invitación/asignación.
"""
from django.core import mail
from django.test import TestCase
from rest_framework.test import APIClient

from apps.usuarios.modelo import Usuario
from apps.usuarios.tokens import crear_tokens_para
from apps.tareas.modelo import Tarea
from apps.proyectos.modelo import Proyecto

from .modelo import Comparticion

COMPARTIR_URL = '/api/v1/compartir/'


class BaseComparticionTest(TestCase):

    def setUp(self):
        self.api = APIClient()
        self.dueno = self.crear_usuario('ana@orbit.local', 'Ana Perez')
        self.invitado = self.crear_usuario('luis@orbit.local', 'Luis Soto')
        self.api.credentials(
            HTTP_AUTHORIZATION=f"Bearer {crear_tokens_para(self.dueno)['access']}"
        )
        self.proyecto = Proyecto(
            nombre='Lanzamiento web', descripcion='', color='#00E5FF',
            usuario=self.dueno,
        )
        self.proyecto.save()
        self.tarea = Tarea(
            titulo='Preparar la demo', usuario=self.dueno,
        )
        self.tarea.save()

    def crear_usuario(self, correo, nombre, contrasena='Prueba#123'):
        usuario = Usuario(nombre_completo=nombre, correo=correo)
        usuario.set_contrasena(contrasena)
        usuario.save()
        return usuario

    def compartir_proyecto(self, correo=None):
        return self.api.post(COMPARTIR_URL, {
            'correo': correo or 'luis@orbit.local',
            'tipo_objeto': 'proyecto',
            'objeto_id': str(self.proyecto.id),
            'permiso': 'editar',
        })


class CorreosDeComparticionTest(BaseComparticionTest):

    def test_invitar_proyecto_envia_correo(self):
        respuesta = self.compartir_proyecto()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ['luis@orbit.local'])
        self.assertIn('Lanzamiento web', correo.subject)
        self.assertIn('Ana Perez', correo.body)

    def test_asignar_tarea_envia_correo(self):
        respuesta = self.api.post(COMPARTIR_URL, {
            'correo': 'luis@orbit.local',
            'tipo_objeto': 'tarea',
            'objeto_id': str(self.tarea.id),
            'permiso': 'editar',
        })

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertIn('Preparar la demo', correo.subject)
        self.assertIn('Ana Perez', correo.body)

    def test_cambiar_permiso_no_reenvia_correo(self):
        self.compartir_proyecto()
        comparticion = Comparticion.objects.get()

        respuesta = self.api.patch(
            f"{COMPARTIR_URL}{comparticion.id}/", {'permiso': 'administrar'}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_compartir_duplicado_no_reenvia_correo(self):
        self.compartir_proyecto()
        self.compartir_proyecto()

        self.assertEqual(len(mail.outbox), 1)


class ValidacionComparticionTest(BaseComparticionTest):

    def test_rechaza_correo_no_registrado(self):
        respuesta = self.api.post(COMPARTIR_URL, {
            'correo': 'nadie@orbit.local',
            'tipo_objeto': 'proyecto',
            'objeto_id': str(self.proyecto.id),
            'permiso': 'ver',
        })

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(len(mail.outbox), 0)

    def test_no_comparte_consigo_mismo(self):
        respuesta = self.api.post(COMPARTIR_URL, {
            'correo': 'ana@orbit.local',
            'tipo_objeto': 'proyecto',
            'objeto_id': str(self.proyecto.id),
            'permiso': 'ver',
        })

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_el_invitado_ve_su_comparticion(self):
        self.compartir_proyecto()

        self.api.credentials(
            HTTP_AUTHORIZATION=f"Bearer {crear_tokens_para(self.invitado)['access']}"
        )
        respuesta = self.api.get(f'{COMPARTIR_URL}conmigo/')

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.json()), 1)
        self.assertEqual(respuesta.json()[0]['titulo'], 'Lanzamiento web')
