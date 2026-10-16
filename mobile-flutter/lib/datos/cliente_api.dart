import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../nucleo/configuracion.dart';

class ClienteApi {
  ClienteApi({this.onSesionInvalida});

  final void Function()? onSesionInvalida;

  static const String _claveToken = 'orbit_access_token';

  Dio? _dio;

  Dio get dio {
    _dio ??= _crear();
    return _dio!;
  }

  Dio _crear() {
    final cliente = Dio(
      BaseOptions(
        baseUrl: Configuracion.urlBase,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    cliente.interceptors.add(
      InterceptorsWrapper(
        onRequest: (opciones, handler) async {
          final token = await leerToken();
          if (token != null && token.isNotEmpty) {
            opciones.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(opciones);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401) {
            final token = await leerToken();
            if (token != null && token.isNotEmpty) {
              await borrarToken();
              onSesionInvalida?.call();
            }
          }
          handler.next(error);
        },
      ),
    );

    return cliente;
  }

  Future<String?> leerToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_claveToken);
  }

  Future<bool> haySesion() async {
    final token = await leerToken();
    return token != null && token.isNotEmpty;
  }

  Future<void> guardarToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_claveToken, token);
  }

  Future<void> borrarToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_claveToken);
  }
}
