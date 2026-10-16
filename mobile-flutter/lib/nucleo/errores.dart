import 'package:dio/dio.dart';

class FallaDeOperacion implements Exception {
  FallaDeOperacion(this.mensaje);

  final String mensaje;

  @override
  String toString() => mensaje;
}

String mensajeDeError(Object error) {
  if (error is DioException) {
    final datos = error.response?.data;
    if (datos is Map<String, dynamic>) {
      if (datos['error'] is String && (datos['error'] as String).isNotEmpty) {
        return datos['error'] as String;
      }
      if (datos['detail'] is String && (datos['detail'] as String).isNotEmpty) {
        return datos['detail'] as String;
      }
      if (datos['mensaje'] is String && (datos['mensaje'] as String).isNotEmpty) {
        return datos['mensaje'] as String;
      }
      final primerCampo = datos.values.whereType<String>().firstOrNull;
      if (primerCampo != null && primerCampo.isNotEmpty) {
        return primerCampo;
      }
    }
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
        return 'No se pudo conectar con el servidor.';
      case DioExceptionType.badResponse:
        return 'El servidor rechazó la petición.';
      default:
        return 'Ocurrió un error inesperado.';
    }
  }
  return 'No se pudo completar la operación.';
}
