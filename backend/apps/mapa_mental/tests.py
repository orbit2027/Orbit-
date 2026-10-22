"""
Pruebas del módulo de mapa mental: forma/color de nodos y conversión masiva.
"""
from django.test import TestCase
from rest_framework.test import APIClient

from apps.usuarios.modelo import Usuario
from apps.usuarios.tokens import crear_tokens_para
from apps.tareas.modelo import Tarea

from .modelo import NodoMapa

MAPA_URL = '/api/v1/mapa-mental/'
NODOS_URL = '/api/v1/mapa-mental/nodos/'
CONVERTIR_LOTE_URL = '/api/v1/mapa-mental/convertir-tarea/'


class BaseMapaTest(TestCase):

    def setUp(self):
        self.api = APIClient()
        self.usuario = self.crear_usuario('ana@orbit.local', 'Ana Perez')
        otro = self.crear_usuario('luis@orbit.local', 'Luis Soto')
        self.api.credentials(
            HTTP_AUTHORIZATION=f"Bearer {crear_tokens_para(self.usuario)['access']}"
        )
        self.nodo_a = self.crear_nodo('Idea uno')
        self.nodo_b = self.crear_nodo('Idea dos')
        self.nodo_luis = self.crear_nodo('Idea ajena', usuario=otro)

    def crear_usuario(self, correo, nombre, contrasena='Prueba#123'):
        usuario = Usuario(nombre_completo=nombre, correo=correo)
        usuario.set_contrasena(contrasena)
        usuario.save()
        return usuario

    def crear_nodo(self, texto, usuario=None):
        nodo = NodoMapa(texto=texto, usuario=usuario or self.usuario)
        nodo.save()
        return nodo


class FormaYColorTextoTest(BaseMapaTest):

    def test_crea_nodo_con_forma_y_color_texto(self):
        respuesta = self.api.post(NODOS_URL, {
            'texto': 'Estrella',
            'color': '#FF4D4D',
            'color_texto': '#FFFFFF',
            'forma': 'star',
            'posicion_x': 10,
            'posicion_y': 20,
        })
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertEqual(datos['forma'], 'star')
        self.assertEqual(datos['color_texto'], '#FFFFFF')

    def test_forma_invalida_se_rechaza(self):
        respuesta = self.api.post(NODOS_URL, {
            'texto': 'Forma mala',
            'forma': 'circulo',
        })
        self.assertEqual(respuesta.status_code, 400)

    def test_edita_forma_y_color_texto(self):
        respuesta = self.api.patch(
            f'{NODOS_URL}{self.nodo_a.id}/',
            {'forma': 'hexagon', 'color_texto': '#00E5FF'}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['forma'], 'hexagon')
        self.assertEqual(respuesta.json()['color_texto'], '#00E5FF')

    def test_el_mapa_incluye_forma_y_color_texto(self):
        respuesta = self.api.get(MAPA_URL)
        nodos = respuesta.json()['nodos']
        formas = {n['forma'] for n in nodos}
        self.assertIn('ellipse', formas)


class ConversionMasivaTest(BaseMapaTest):

    def test_convierte_toda_la_seleccion(self):
        respuesta = self.api.post(CONVERTIR_LOTE_URL, {
            'nodos': [str(self.nodo_a.id), str(self.nodo_b.id)],
            'descripcion': 'Desde el mapa',
            'etiqueta': 'Trabajo',
            'color_etiqueta': '#00E5FF',
        })
        self.assertEqual(respuesta.status_code, 201)
        datos = respuesta.json()
        self.assertEqual(len(datos['creadas']), 2)
        self.assertEqual(datos['omitidas'], [])

        tareas = Tarea.objects.filter(usuario=self.usuario)
        self.assertEqual(tareas.count(), 2)
        titulos = set(tareas.values_list('titulo', flat=True))
        self.assertEqual(titulos, {'Idea uno', 'Idea dos'})
        tarea = tareas.get(titulo='Idea uno')
        self.assertEqual(tarea.etiqueta, 'Trabajo')
        self.assertEqual(tarea.origen_nodo, str(self.nodo_a.id))

    def test_omite_nodos_ya_convertidos_y_ajenos(self):
        self.api.post(f'{NODOS_URL}{self.nodo_a.id}/convertir-tarea/', {})

        respuesta = self.api.post(CONVERTIR_LOTE_URL, {
            'nodos': [
                str(self.nodo_a.id),
                str(self.nodo_b.id),
                str(self.nodo_luis.id),
            ],
        })

        datos = respuesta.json()
        self.assertEqual(len(datos['creadas']), 1)
        self.assertEqual(len(datos['omitidas']), 2)

    def test_nodo_convertido_marca_su_estado(self):
        self.api.post(CONVERTIR_LOTE_URL, {'nodos': [str(self.nodo_a.id)]})
        self.nodo_a.refresh_from_db()
        self.assertTrue(self.nodo_a.convertido_en_tarea)

    def test_lista_vacia_se_rechaza(self):
        respuesta = self.api.post(CONVERTIR_LOTE_URL, {'nodos': []})
        self.assertEqual(respuesta.status_code, 400)

    def test_mas_de_100_nodos_se_rechaza(self):
        ids = [str(self.nodo_a.id)] * 101
        respuesta = self.api.post(CONVERTIR_LOTE_URL, {'nodos': ids})
        self.assertEqual(respuesta.status_code, 400)

    def test_conversion_unica_sigue_funcionando(self):
        respuesta = self.api.post(
            f'{NODOS_URL}{self.nodo_a.id}/convertir-tarea/',
            {'etiqueta': 'Estudio', 'fecha_limite': '2026-12-01'}
        )
        self.assertEqual(respuesta.status_code, 201)
        tarea = Tarea.objects.get(id=respuesta.json()['tarea_id'])
        self.assertEqual(tarea.etiqueta, 'Estudio')
        self.assertEqual(str(tarea.fecha_limite), '2026-12-01')
