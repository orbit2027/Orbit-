import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../datos/cliente_api.dart';
import '../datos/repositorios/auth_repositorio.dart';
import '../datos/repositorios/proyectos_repositorio.dart';
import '../datos/repositorios/tareas_repositorio.dart';
import 'auth_controlador.dart';

final clienteApiProvider = Provider<ClienteApi>((ref) {
  return ClienteApi(
    onSesionInvalida: () =>
        ref.read(authProvider.notifier).cerrarSesionPorExpiracion(),
  );
});

final authRepositorioProvider = Provider<AuthRepositorio>((ref) {
  final cliente = ref.watch(clienteApiProvider);
  return AuthRepositorio(cliente.dio, cliente);
});

final tareasRepositorioProvider = Provider<TareasRepositorio>((ref) {
  return TareasRepositorio(ref.watch(clienteApiProvider).dio);
});

final proyectosRepositorioProvider = Provider<ProyectosRepositorio>((ref) {
  return ProyectosRepositorio(ref.watch(clienteApiProvider).dio);
});
