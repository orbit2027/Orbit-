import 'package:dio/dio.dart';

import '../../nucleo/errores.dart';
import '../modelos/tarea.dart';

class TareasRepositorio {
  TareasRepositorio(this._dio);

  final Dio _dio;

  Future<List<Tarea>> listar() async {
    try {
      final respuesta = await _dio.get('/tareas/');
      final lista = respuesta.data as List<dynamic>;
      return lista
          .map((elemento) => Tarea.desdeJson(elemento as Map<String, dynamic>))
          .toList();
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }

  Future<Tarea> crear(Map<String, dynamic> datos) async {
    try {
      final respuesta = await _dio.post('/tareas/', data: datos);
      return Tarea.desdeJson(respuesta.data as Map<String, dynamic>);
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }

  Future<Tarea> actualizar(String id, Map<String, dynamic> datos) async {
    try {
      final respuesta = await _dio.patch('/tareas/$id/', data: datos);
      return Tarea.desdeJson(respuesta.data as Map<String, dynamic>);
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }

  Future<Tarea> cambiarEstado(String id, String estado) {
    return actualizar(id, {'estado': estado});
  }

  Future<void> eliminar(String id) async {
    try {
      await _dio.delete('/tareas/$id/');
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }
}
