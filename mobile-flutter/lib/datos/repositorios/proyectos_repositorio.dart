import 'package:dio/dio.dart';

import '../../nucleo/errores.dart';
import '../modelos/proyecto.dart';

class ProyectosRepositorio {
  ProyectosRepositorio(this._dio);

  final Dio _dio;

  Future<List<Proyecto>> listar() async {
    try {
      final respuesta = await _dio.get('/proyectos/');
      final lista = respuesta.data as List<dynamic>;
      return lista
          .map((elemento) => Proyecto.desdeJson(elemento as Map<String, dynamic>))
          .toList();
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }

  Future<Proyecto> crear(Map<String, dynamic> datos) async {
    try {
      final respuesta = await _dio.post('/proyectos/', data: datos);
      return Proyecto.desdeJson(respuesta.data as Map<String, dynamic>);
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }

  Future<Proyecto> actualizar(String id, Map<String, dynamic> datos) async {
    try {
      final respuesta = await _dio.patch('/proyectos/$id/', data: datos);
      return Proyecto.desdeJson(respuesta.data as Map<String, dynamic>);
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }

  Future<Proyecto> alternarArchivado(Proyecto proyecto) async {
    return actualizar(proyecto.id, {
      'estado': proyecto.estaArchivado ? Proyecto.activo : Proyecto.archivado,
    });
  }

  Future<void> eliminar(String id) async {
    try {
      await _dio.delete('/proyectos/$id/');
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }
}
