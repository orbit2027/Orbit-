"""
Pruebas del módulo de compartición: invitaciones por correo, aceptación,
permisos y acceso efectivo a tareas y proyectos.
"""
from django.core import mail
from django.test import TestCase
from rest_framework.test import APIClient

from apps.usuarios.modelo import Usuario
from apps.usuarios.tokens import crear_tokens_para
from apps.tareas.modelo import Tarea
from apps.proyectos.modelo import Proyecto

from .modelo import Comparticion, Invitacion

COMPARTIR_URL = '/api/v1/compartir/'
INVITACIONES_URL = '/api/v1/compartir/invitaciones/'


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

    def compartir(self, tipo='proyecto', objeto_id=None, correo=None, permiso='editar'):
        return self.api.post(COMPARTIR_URL, {
            'correo': correo or 'luis@orbit.local',
            'tipo_objeto': tipo,
            'objeto_id': str(objeto_id or self.proyecto.id),
            'permiso': permiso,
        })

    def invitar_proyecto(self, correo=None, permiso='editar'):
        return self.compartir('proyecto', self.proyecto.id, correo, permiso)

    def autenticar(self, usuario):
        self.api.credentials(
            HTTP_AUTHORIZATION=f"Bearer {crear_tokens_para(usuario)['access']}"
        )

    def aceptar(self, referencia, aceptar=True):
        return self.api.post(
            f'{INVITACIONES_URL}{referencia}/responder/', {'aceptar': aceptar}
        )


class InvitacionPorCorreoTest(BaseComparticionTest):

    def test_invitar_crea_invitacion_pendiente_y_envia_correo(self):
        respuesta = self.invitar_proyecto()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['estado'], 'pendiente')
        self.assertEqual(Invitacion.objects.filter(estado='pendiente').count(), 1)
        self.assertEqual(Comparticion.objects.count(), 0)

        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ['luis@orbit.local'])
        self.assertIn('Lanzamiento web', correo.subject)
        self.assertIn('Ana Perez', correo.body)
        self.assertIn('/vistas/invitaciones.html?invitacion=', correo.body)
        self.assertIn('Aceptar invitación', correo.body)
        self.assertTrue(respuesta.json()['correo_enviado'])

    def test_puede_invitar_a_un_correo_sin_cuenta(self):
        respuesta = self.invitar_proyecto(correo='nuevo@orbit.local')

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()['tiene_cuenta'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['nuevo@orbit.local'])

    def test_invitar_tarea_envia_correo_con_el_titulo(self):
        respuesta = self.compartir('tarea', self.tarea.id)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Preparar la demo', mail.outbox[0].subject)

    def test_duplicado_pendiente_no_reenvia_correo_y_actualiza_permiso(self):
        self.invitar_proyecto()
        respuesta = self.invitar_proyecto()

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Invitacion.objects.get().permiso, 'editar')
        self.assertFalse(respuesta.json()['correo_enviado'])

    def test_invitar_a_quien_ya_tiene_acceso_solo_actualiza_permiso(self):
        self.invitar_proyecto(permiso='ver')
        invitacion = Invitacion.objects.get()
        self.autenticar(self.invitado)
        self.aceptar(invitacion.id)
        self.autenticar(self.dueno)
        mail.outbox.clear()

        respuesta = self.invitar_proyecto(permiso='administrar')

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()['ya_tiene_acceso'])
        self.assertFalse(respuesta.json()['correo_enviado'])
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Comparticion.objects.get().permiso, 'administrar')

    def test_reinvitar_una_rechazada_la_reactiva_y_envia_correo(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()
        self.autenticar(self.invitado)
        self.aceptar(invitacion.id, aceptar=False)
        self.autenticar(self.dueno)
        mail.outbox.clear()

        respuesta = self.invitar_proyecto(permiso='ver')

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['estado'], 'pendiente')
        self.assertTrue(respuesta.json()['correo_enviado'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Invitacion.objects.get().estado, 'pendiente')

    def test_reenviar_invitacion_envia_otro_correo(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()

        respuesta = self.api.post(f'{INVITACIONES_URL}{invitacion.id}/reenviar/')

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)

    def test_no_comparte_consigo_mismo(self):
        respuesta = self.invitar_proyecto(correo='ana@orbit.local')

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_no_permite_invitar_sin_permiso(self):
        self.autenticar(self.invitado)

        respuesta = self.invitar_proyecto(correo='otro@orbit.local')

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)


class AceptarRechazarInvitacionTest(BaseComparticionTest):

    def test_invitado_no_ve_la_tarea_hasta_aceptar(self):
        self.compartir('tarea', self.tarea.id)
        self.autenticar(self.invitado)

        respuesta = self.api.get('/api/v1/tareas/')

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), [])

    def test_aceptar_crea_acceso_y_la_tarea_aparece(self):
        self.compartir('tarea', self.tarea.id)
        invitacion = Invitacion.objects.get()
        self.autenticar(self.invitado)

        respuesta = self.aceptar(invitacion.id)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['mensaje'], 'Invitación aceptada')
        self.assertEqual(Comparticion.objects.count(), 1)
        invitacion.refresh_from_db()
        self.assertEqual(invitacion.estado, 'aceptada')

        tareas = self.api.get('/api/v1/tareas/').json()
        self.assertEqual([t['titulo'] for t in tareas], ['Preparar la demo'])
        # Aviso al dueño de que aceptaron.
        self.assertEqual(len(mail.outbox), 2)

    def test_aceptar_con_token_del_correo(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()
        self.autenticar(self.invitado)

        respuesta = self.aceptar(invitacion.token)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Comparticion.objects.count(), 1)

    def test_rechazar_no_crea_acceso(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()
        self.autenticar(self.invitado)

        respuesta = self.aceptar(invitacion.id, aceptar=False)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Comparticion.objects.count(), 0)
        invitacion.refresh_from_db()
        self.assertEqual(invitacion.estado, 'rechazada')
        self.assertEqual(self.api.get('/api/v1/proyectos/').json(), [])

    def test_otro_usuario_no_puede_aceptar_la_invitacion(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()
        otro = self.crear_usuario('otro@orbit.local', 'Otro Usuario')
        self.autenticar(otro)

        respuesta = self.aceptar(invitacion.id)

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(Comparticion.objects.count(), 0)

    def test_no_se_puede_aceptar_dos_veces(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()
        self.autenticar(self.invitado)
        self.aceptar(invitacion.id)

        respuesta = self.aceptar(invitacion.id)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['mensaje'], 'Ya habías aceptado esta invitación.')
        self.assertEqual(Comparticion.objects.count(), 1)

    def test_invitacion_de_elemento_eliminado_devuelve_404(self):
        self.compartir('tarea', self.tarea.id)
        invitacion = Invitacion.objects.get()
        self.tarea.delete()
        self.autenticar(self.invitado)

        respuesta = self.aceptar(invitacion.id)

        self.assertEqual(respuesta.status_code, 404)


class ListadosTest(BaseComparticionTest):

    def test_mis_invitaciones_solo_muestra_pendientes(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()
        self.autenticar(self.invitado)

        pendientes = self.api.get(INVITACIONES_URL).json()
        self.assertEqual(len(pendientes), 1)
        self.assertEqual(pendientes[0]['titulo'], 'Lanzamiento web')
        self.assertEqual(pendientes[0]['propietario'], 'Ana Perez')
        self.assertEqual(pendientes[0]['tipo_objeto'], 'proyecto')

        self.aceptar(invitacion.id)
        self.assertEqual(self.api.get(INVITACIONES_URL).json(), [])

    def test_lista_del_objeto_mezcla_accesos_e_invitaciones(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()
        self.autenticar(self.invitado)
        self.aceptar(invitacion.id)

        otro = self.crear_usuario('otro@orbit.local', 'Otro Usuario')
        self.autenticar(self.dueno)
        self.compartir('proyecto', self.proyecto.id, correo=otro.correo)

        respuesta = self.api.get(
            f'/api/v1/compartir/lista/proyecto/{self.proyecto.id}/'
        )

        self.assertEqual(respuesta.status_code, 200)
        estados = {d['correo']: d['estado'] for d in respuesta.json()}
        self.assertEqual(estados['luis@orbit.local'], 'aceptada')
        self.assertEqual(estados['otro@orbit.local'], 'pendiente')

    def test_dueno_puede_cambiar_permiso_y_quitar_acceso(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()
        self.autenticar(self.invitado)
        self.aceptar(invitacion.id)
        comparticion = Comparticion.objects.get()
        self.autenticar(self.dueno)

        cambio = self.api.patch(
            f'{COMPARTIR_URL}{comparticion.id}/', {'permiso': 'administrar'}
        )
        self.assertEqual(cambio.status_code, 200)
        self.assertEqual(cambio.json()['permiso'], 'administrar')

        eliminado = self.api.delete(f'{COMPARTIR_URL}{comparticion.id}/')
        self.assertEqual(eliminado.status_code, 200)
        self.assertEqual(Comparticion.objects.count(), 0)

    def test_puede_cancelar_una_invitacion_pendiente(self):
        self.invitar_proyecto()
        invitacion = Invitacion.objects.get()

        respuesta = self.api.delete(f'{INVITACIONES_URL}{invitacion.id}/')

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Invitacion.objects.count(), 0)
