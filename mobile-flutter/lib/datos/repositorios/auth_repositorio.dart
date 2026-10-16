import 'package:dio/dio.dart';

import '../../nucleo/errores.dart';
import '../cliente_api.dart';
import '../modelos/usuario.dart';

class AuthRepositorio {
  AuthRepositorio(this._dio, this._cliente);

  final Dio _dio;
  final ClienteApi _cliente;

  Future<Usuario> iniciarSesion({
    required String correo,
    required String contrasena,
  }) async {
    try {
      final respuesta = await _dio.post(
        '/usuarios/login/',
        data: {'correo': correo, 'contrasena': contrasena},
      );
      final datos = respuesta.data as Map<String, dynamic>;
      final tokens = datos['tokens'] as Map<String, dynamic>;
      await _cliente.guardarToken(tokens['access'] as String);
      return Usuario.desdeJson(datos['usuario'] as Map<String, dynamic>);
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }

  Future<Usuario> registrar({
    required String nombreCompleto,
    required String correo,
    required String contrasena,
  }) async {
    try {
      final respuesta = await _dio.post(
        '/usuarios/registro/',
        data: {
          'nombre_completo': nombreCompleto,
          'correo': correo,
          'contrasena': contrasena,
        },
      );
      final datos = respuesta.data as Map<String, dynamic>;
      final tokens = datos['tokens'] as Map<String, dynamic>;
      await _cliente.guardarToken(tokens['access'] as String);
      return Usuario.desdeJson(datos['usuario'] as Map<String, dynamic>);
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }

  Future<Usuario> perfil() async {
    try {
      final respuesta = await _dio.get('/usuarios/perfil/');
      return Usuario.desdeJson(
        respuesta.data as Map<String, dynamic>,
      );
    } catch (error) {
      throw FallaDeOperacion(mensajeDeError(error));
    }
  }

  Future<void> cerrarSesion() async {
    try {
      await _dio.post('/usuarios/logout/');
    } finally {
      await _cliente.borrarToken();
    }
  }
}
