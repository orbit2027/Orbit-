import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../datos/modelos/proyecto.dart';
import 'proveedores.dart';

class ProyectosControlador extends AsyncNotifier<List<Proyecto>> {
  @override
  Future<List<Proyecto>> build() {
    return ref.read(proyectosRepositorioProvider).listar();
  }

  Future<void> refrescar() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => ref.read(proyectosRepositorioProvider).listar(),
    );
  }

  Future<void> crear(Map<String, dynamic> datos) async {
    await ref.read(proyectosRepositorioProvider).crear(datos);
    await refrescar();
  }

  Future<void> actualizar(String id, Map<String, dynamic> datos) async {
    await ref.read(proyectosRepositorioProvider).actualizar(id, datos);
    await refrescar();
  }

  Future<void> alternarArchivado(Proyecto proyecto) async {
    await ref
        .read(proyectosRepositorioProvider)
        .alternarArchivado(proyecto);
    await refrescar();
  }

  Future<void> eliminar(String id) async {
    await ref.read(proyectosRepositorioProvider).eliminar(id);
    await refrescar();
  }
}

final proyectosProvider =
    AsyncNotifierProvider<ProyectosControlador, List<Proyecto>>(
  ProyectosControlador.new,
);
