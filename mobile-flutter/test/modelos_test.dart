import 'package:flutter_test/flutter_test.dart';
import 'package:orbit_movil/datos/modelos/proyecto.dart';
import 'package:orbit_movil/datos/modelos/tarea.dart';
import 'package:orbit_movil/datos/modelos/usuario.dart';

void main() {
  group('Usuario', () {
    test('desdeJson parsea la respuesta del backend', () {
      final usuario = Usuario.desdeJson({
        'id': '7',
        'nombre_completo': 'Ana Torres',
        'correo': 'ana@orbit.local',
        'rol': 'administrador',
        'fecha_registro': '2026-01-15T10:00:00Z',
      });

      expect(usuario.id, '7');
      expect(usuario.nombreCompleto, 'Ana Torres');
      expect(usuario.correo, 'ana@orbit.local');
      expect(usuario.rol, 'administrador');
      expect(usuario.fechaRegistro, '2026-01-15T10:00:00Z');
    });

    test('desdeJson tolera campos ausentes', () {
      final usuario = Usuario.desdeJson(const {});

      expect(usuario.id, '');
      expect(usuario.rol, 'usuario');
      expect(usuario.fechaRegistro, isNull);
    });

    test('iniciales de uno y dos nombres', () {
      const uno = Usuario(
        id: '1',
        nombreCompleto: 'Carlos',
        correo: 'c@x.com',
        rol: 'usuario',
      );
      const dos = Usuario(
        id: '2',
        nombreCompleto: 'Ana María Torres',
        correo: 'a@x.com',
        rol: 'usuario',
      );

      expect(uno.iniciales, 'C');
      expect(dos.iniciales, 'AT');
    });
  });

  group('Tarea', () {
    test('desdeJson parsea con valores por defecto', () {
      final tarea = Tarea.desdeJson({
        'id': 'abc',
        'titulo': 'Revisar diseño',
      });

      expect(tarea.id, 'abc');
      expect(tarea.titulo, 'Revisar diseño');
      expect(tarea.estado, Tarea.porHacer);
      expect(tarea.colorEtiqueta, '#00E5FF');
      expect(tarea.fechaLimite, isNull);
      expect(tarea.proyecto, '');
    });

    test('desdeJson parsea campos completos', () {
      final tarea = Tarea.desdeJson({
        'id': 'abc',
        'titulo': 'Diseñar portada',
        'descripcion': 'Colores orbit',
        'estado': 'en_progreso',
        'etiqueta': 'Diseño',
        'color_etiqueta': '#A78BFA',
        'fecha_limite': '2026-11-01',
        'origen_nodo': 'n1',
        'proyecto': 'p9',
        'usuario': 'u3',
        'fecha_creacion': '2026-10-01T00:00:00Z',
      });

      expect(tarea.estado, 'en_progreso');
      expect(tarea.etiqueta, 'Diseño');
      expect(tarea.fechaLimite, '2026-11-01');
      expect(tarea.proyecto, 'p9');
      expect(tarea.etiquetaEstado, 'En progreso');
    });
  });

  group('Proyecto', () {
    test('avance calcula el porcentaje de tareas completadas', () {
      final proyecto = Proyecto.desdeJson({
        'id': 'p1',
        'nombre': 'Lanzamiento',
        'descripcion': '',
        'color': '#00C48C',
        'estado': 'activo',
        'usuario': 'u1',
        'tareas_totales': 4,
        'tareas_completadas': 1,
        'tareas_activas': 3,
      });

      expect(proyecto.avance, 0.25);
      expect(proyecto.estaArchivado, isFalse);
    });

    test('avance es 0 sin tareas y detecta archivado', () {
      final proyecto = Proyecto.desdeJson({
        'id': 'p2',
        'nombre': 'Viejo',
        'descripcion': '',
        'color': '#FF4D4D',
        'estado': 'archivado',
        'usuario': 'u1',
      });

      expect(proyecto.avance, 0);
      expect(proyecto.estaArchivado, isTrue);
    });
  });
}
