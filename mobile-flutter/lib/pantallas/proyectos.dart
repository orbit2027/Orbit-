import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../datos/modelos/proyecto.dart';
import '../estado/proyectos_controlador.dart';
import '../nucleo/tema.dart';
import 'editor_proyecto.dart';

Color parsearColorHex(String hex) {
  var valor = hex.replaceAll('#', '').trim();
  if (valor.length == 6) valor = 'FF$valor';
  final numero = int.tryParse(valor, radix: 16);
  if (numero == null) return colorOrbitAcento;
  return Color(numero);
}

String colorAHex(Color color) {
  final componentes = [color.r, color.g, color.b];
  final hex = componentes
      .map((c) => (c * 255).round().toRadixString(16).padLeft(2, '0'))
      .join();
  return '#${hex.toUpperCase()}';
}

class ProyectosPantalla extends ConsumerStatefulWidget {
  const ProyectosPantalla({super.key});

  @override
  ConsumerState<ProyectosPantalla> createState() => _ProyectosPantallaState();
}

class _ProyectosPantallaState extends ConsumerState<ProyectosPantalla> {
  bool _mostrarArchivados = false;

  Future<void> _abrirEditor({Proyecto? proyecto}) async {
    final guardado = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => EditorProyectoPantalla(proyecto: proyecto)),
    );
    if (guardado == true) {
      ref.read(proyectosProvider.notifier).refrescar();
    }
  }

  Future<void> _alternar(Proyecto proyecto) async {
    try {
      await ref.read(proyectosProvider.notifier).alternarArchivado(proyecto);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.toString())),
        );
      }
    }
  }

  Future<void> _eliminar(Proyecto proyecto) async {
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: const Text('Eliminar proyecto'),
        content: Text(
          '¿Eliminar "${proyecto.nombre}"? Las tareas quedarán sin proyecto.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(contexto).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(contexto).pop(true),
            style: FilledButton.styleFrom(backgroundColor: colorOrbitError),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (confirmado == true) {
      try {
        await ref.read(proyectosProvider.notifier).eliminar(proyecto.id);
      } catch (error) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(error.toString())),
          );
        }
      }
    }
  }

  Widget _tarjeta(Proyecto proyecto) {
    final color = parsearColorHex(proyecto.color);
    final archivado = proyecto.estaArchivado;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => _abrirEditor(proyecto: proyecto),
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(width: 6, color: color),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(14, 14, 6, 14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              proyecto.nombre,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                          if (archivado)
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 3,
                              ),
                              decoration: BoxDecoration(
                                color: colorSecundarioTexto.withValues(alpha: 0.16),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: const Text(
                                'Archivado',
                                style: TextStyle(fontSize: 11, color: colorSecundarioTexto),
                              ),
                            ),
                          PopupMenuButton<String>(
                            icon: const Icon(Icons.more_vert, size: 20),
                            onSelected: (valor) {
                              if (valor == 'editar') {
                                _abrirEditor(proyecto: proyecto);
                              } else if (valor == 'archivar') {
                                _alternar(proyecto);
                              } else {
                                _eliminar(proyecto);
                              }
                            },
                            itemBuilder: (contexto) => [
                              const PopupMenuItem(value: 'editar', child: Text('Editar')),
                              PopupMenuItem(
                                value: 'archivar',
                                child: Text(archivado ? 'Desarchivar' : 'Archivar'),
                              ),
                              const PopupMenuItem(value: 'eliminar', child: Text('Eliminar')),
                            ],
                          ),
                        ],
                      ),
                      if (proyecto.descripcion.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          proyecto.descripcion,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 13,
                            color: colorSecundarioTexto,
                          ),
                        ),
                      ],
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: LinearProgressIndicator(
                                value: proyecto.avance,
                                minHeight: 6,
                                backgroundColor: const Color(0xFF1E293B),
                                valueColor: AlwaysStoppedAnimation<Color>(color),
                              ),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Text(
                            '${proyecto.tareasCompletadas}/${proyecto.tareasTotales}',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: colorSecundarioTexto,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final proyectosAsync = ref.watch(proyectosProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Proyectos')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _abrirEditor(),
        icon: const Icon(Icons.add),
        label: const Text('Nuevo'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
            child: Row(
              children: [
                _FiltroProyecto(
                  texto: 'Activos',
                  activo: !_mostrarArchivados,
                  onTap: () => setState(() => _mostrarArchivados = false),
                ),
                const SizedBox(width: 8),
                _FiltroProyecto(
                  texto: 'Archivados',
                  activo: _mostrarArchivados,
                  onTap: () => setState(() => _mostrarArchivados = true),
                ),
              ],
            ),
          ),
          Expanded(
            child: proyectosAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.cloud_off, size: 48, color: colorSecundarioTexto),
                      const SizedBox(height: 12),
                      Text(
                        error.toString(),
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: colorSecundarioTexto),
                      ),
                      const SizedBox(height: 16),
                      OutlinedButton(
                        onPressed: () =>
                            ref.read(proyectosProvider.notifier).refrescar(),
                        child: const Text('Reintentar'),
                      ),
                    ],
                  ),
                ),
              ),
              data: (proyectos) {
                final visibles = proyectos
                    .where((proyecto) => proyecto.estaArchivado == _mostrarArchivados)
                    .toList();
                if (visibles.isEmpty) {
                  return RefreshIndicator(
                    onRefresh: () => ref.read(proyectosProvider.notifier).refrescar(),
                    child: ListView(
                      children: [
                        const SizedBox(height: 80),
                        const Icon(Icons.folder_open,
                            size: 56, color: colorSecundarioTexto),
                        const SizedBox(height: 12),
                        Text(
                          _mostrarArchivados
                              ? 'No hay proyectos archivados'
                              : 'Crea tu primer proyecto',
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: colorSecundarioTexto),
                        ),
                      ],
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () => ref.read(proyectosProvider.notifier).refrescar(),
                  child: ListView.separated(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(16, 4, 16, 88),
                    itemCount: visibles.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (contexto, indice) => _tarjeta(visibles[indice]),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _FiltroProyecto extends StatelessWidget {
  const _FiltroProyecto({
    required this.texto,
    required this.activo,
    required this.onTap,
  });

  final String texto;
  final bool activo;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(texto),
      selected: activo,
      onSelected: (_) => onTap(),
      selectedColor: colorOrbitAcento.withValues(alpha: 0.18),
      labelStyle: TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: activo ? colorOrbitAcento : colorSecundarioTexto,
      ),
      side: BorderSide(color: activo ? colorOrbitAcento : const Color(0xFF334155)),
    );
  }
}
