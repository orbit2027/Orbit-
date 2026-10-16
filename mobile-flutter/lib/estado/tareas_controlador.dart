import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../datos/modelos/tarea.dart';
import 'proveedores.dart';

class TareasControlador extends AsyncNotifier<List<Tarea>> {
  @override
  Future<List<Tarea>> build() {
    return ref.read(tareasRepositorioProvider).listar();
  }

  Future<void> refrescar() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => ref.read(tareasRepositorioProvider).listar(),
    );
  }

  Future<void> crear(Map<String, dynamic> datos) async {
    await ref.read(tareasRepositorioProvider).crear(datos);
    await refrescar();
  }

  Future<void> actualizar(String id, Map<String, dynamic> datos) async {
    await ref.read(tareasRepositorioProvider).actualizar(id, datos);
    await refrescar();
  }

  Future<void> cambiarEstado(String id, String estado) async {
    await ref.read(tareasRepositorioProvider).cambiarEstado(id, estado);
    await refrescar();
  }

  Future<void> eliminar(String id) async {
    await ref.read(tareasRepositorioProvider).eliminar(id);
    await refrescar();
  }
}

final tareasProvider =
    AsyncNotifierProvider<TareasControlador, List<Tarea>>(
  TareasControlador.new,
);
