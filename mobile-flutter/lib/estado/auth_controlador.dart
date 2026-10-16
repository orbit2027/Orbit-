import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../datos/modelos/usuario.dart';
import 'proveedores.dart';

class EstadoAuth {
  const EstadoAuth({
    this.comprobandoSesion = true,
    this.enviando = false,
    this.usuario,
    this.error,
  });

  final bool comprobandoSesion;
  final bool enviando;
  final Usuario? usuario;
  final String? error;

  bool get autenticado => usuario != null;

  EstadoAuth copiarCon({
    bool? comprobandoSesion,
    bool? enviando,
    Usuario? usuario,
    String? error,
    bool borrarUsuario = false,
    bool borrarError = false,
  }) {
    return EstadoAuth(
      comprobandoSesion: comprobandoSesion ?? this.comprobandoSesion,
      enviando: enviando ?? this.enviando,
      usuario: borrarUsuario ? null : (usuario ?? this.usuario),
      error: borrarError ? null : (error ?? this.error),
    );
  }
}

class AuthControlador extends Notifier<EstadoAuth> {
  @override
  EstadoAuth build() => const EstadoAuth();

  Future<void> iniciarSesion({
    required String correo,
    required String contrasena,
  }) async {
    state = state.copiarCon(enviando: true, borrarError: true);
    try {
      final usuario = await ref.read(authRepositorioProvider).iniciarSesion(
            correo: correo,
            contrasena: contrasena,
          );
      state = EstadoAuth(comprobandoSesion: false, usuario: usuario);
    } catch (error) {
      state = state.copiarCon(enviando: false, error: error.toString());
    }
  }

  Future<void> registrar({
    required String nombreCompleto,
    required String correo,
    required String contrasena,
  }) async {
    state = state.copiarCon(enviando: true, borrarError: true);
    try {
      final usuario = await ref.read(authRepositorioProvider).registrar(
            nombreCompleto: nombreCompleto,
            correo: correo,
            contrasena: contrasena,
          );
      state = EstadoAuth(comprobandoSesion: false, usuario: usuario);
    } catch (error) {
      state = state.copiarCon(enviando: false, error: error.toString());
    }
  }

  Future<void> restaurarSesion() async {
    try {
      final usuario = await ref.read(authRepositorioProvider).perfil();
      state = EstadoAuth(comprobandoSesion: false, usuario: usuario);
    } catch (_) {
      state = const EstadoAuth(comprobandoSesion: false);
    }
  }

  Future<void> cerrarSesion() async {
    try {
      await ref.read(authRepositorioProvider).cerrarSesion();
    } finally {
      state = const EstadoAuth(comprobandoSesion: false);
    }
  }

  void cerrarSesionPorExpiracion() {
    state = const EstadoAuth(
      comprobandoSesion: false,
      error: 'Tu sesión expiró. Inicia sesión de nuevo.',
    );
  }

  void limpiarError() {
    if (state.error != null) {
      state = state.copiarCon(borrarError: true);
    }
  }
}

final authProvider =
    NotifierProvider<AuthControlador, EstadoAuth>(AuthControlador.new);
