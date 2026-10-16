import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../datos/modelos/tarea.dart';
import '../estado/tareas_controlador.dart';
import '../nucleo/tema.dart';
import 'editor_tarea.dart';

const estadosTarea = ['por_hacer', 'en_progreso', 'completado'];

String etiquetaEstado(String estado) {
  switch (estado) {
    case 'en_progreso':
      return 'En progreso';
    case 'completado':
      return 'Completado';
    default:
      return 'Por hacer';
  }
}

Color colorEstado(String estado) {
  switch (estado) {
    case 'en_progreso':
      return colorOrbitAdvertencia;
    case 'completado':
      return colorOrbitExito;
    default:
      return colorOrbitAcento;
  }
}

class TareasPantalla extends ConsumerStatefulWidget {
  const TareasPantalla({super.key});

  @override
  ConsumerState<TareasPantalla> createState() => _TareasPantallaState();
}

class _TareasPantallaState extends ConsumerState<TareasPantalla> {
  String _filtro = 'todas';

  List<Tarea> _aplicarFiltro(List<Tarea> tareas) {
    if (_filtro == 'todas') return tareas;
    return tareas.where((tarea) => tarea.estado == _filtro).toList();
  }

  Future<void> _abrirEditor({Tarea? tarea}) async {
    final guardado = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => EditorTareaPantalla(tarea: tarea)),
    );
    if (guardado == true) {
      ref.read(tareasProvider.notifier).refrescar();
    }
  }

  Future<void> _moverA(Tarea tarea, String estado) async {
    if (tarea.estado == estado) return;
    try {
      await ref.read(tareasProvider.notifier).cambiarEstado(tarea.id, estado);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.toString())),
        );
      }
    }
  }

  Future<void> _eliminar(Tarea tarea) async {
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: const Text('Eliminar tarea'),
        content: Text('¿Eliminar "${tarea.titulo}"?'),
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
        await ref.read(tareasProvider.notifier).eliminar(tarea.id);
      } catch (error) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(error.toString())),
          );
        }
      }
    }
  }

  Widget _tarjeta(Tarea tarea) {
    final completada = tarea.estado == 'completado';
    final color = colorEstado(tarea.estado);

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => _abrirEditor(tarea: tarea),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 4,
                    height: 46,
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          tarea.titulo,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                            decoration: completada ? TextDecoration.lineThrough : null,
                            color: completada ? const Color(0xFF94A3B8) : colorOrbitTexto,
                          ),
                        ),
                        if (tarea.descripcion.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            tarea.descripcion,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
                          ),
                        ],
                      ],
                    ),
                  ),
                  PopupMenuButton<String>(
                    icon: const Icon(Icons.more_vert, size: 20),
                    onSelected: (valor) {
                      if (valor == 'editar') {
                        _abrirEditor(tarea: tarea);
                      } else if (valor == 'eliminar') {
                        _eliminar(tarea);
                      } else {
                        _moverA(tarea, valor);
                      }
                    },
                    itemBuilder: (contexto) => [
                      const PopupMenuItem(value: 'editar', child: Text('Editar')),
                      for (final estado in estadosTarea)
                        if (estado != tarea.estado)
                          PopupMenuItem(
                            value: estado,
                            child: Text('Mover a ${etiquetaEstado(estado)}'),
                          ),
                      const PopupMenuItem(value: 'eliminar', child: Text('Eliminar')),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      etiquetaEstado(tarea.estado),
                      style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600),
                    ),
                  ),
                  if (tarea.etiqueta.isNotEmpty) ...[
                    const SizedBox(width: 8),
                    Text(
                      tarea.etiqueta,
                      style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                    ),
                  ],
                  const Spacer(),
                  if (tarea.fechaLimite != null)
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.event, size: 14, color: colorSecundarioTexto),
                        const SizedBox(width: 4),
                        Text(
                          _formatearFecha(tarea.fechaLimite!),
                          style: const TextStyle(fontSize: 12, color: colorSecundarioTexto),
                        ),
                      ],
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatearFecha(String iso) {
    try {
      final fecha = DateTime.parse(iso).toLocal();
      return '${fecha.day.toString().padLeft(2, '0')}/'
          '${fecha.month.toString().padLeft(2, '0')}/${fecha.year}';
    } catch (_) {
      return iso.split('T').first;
    }
  }

  @override
  Widget build(BuildContext context) {
    final tareasAsync = ref.watch(tareasProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Tareas')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _abrirEditor(),
        icon: const Icon(Icons.add),
        label: const Text('Nueva'),
      ),
      body: Column(
        children: [
          SizedBox(
            height: 52,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              children: [
                _FiltroChip(
                  texto: 'Todas',
                  activo: _filtro == 'todas',
                  onTap: () => setState(() => _filtro = 'todas'),
                ),
                for (final estado in estadosTarea)
                  _FiltroChip(
                    texto: etiquetaEstado(estado),
                    activo: _filtro == estado,
                    color: colorEstado(estado),
                    onTap: () => setState(() => _filtro = estado),
                  ),
              ],
            ),
          ),
          Expanded(
            child: tareasAsync.when(
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
                        onPressed: () => ref.read(tareasProvider.notifier).refrescar(),
                        child: const Text('Reintentar'),
                      ),
                    ],
                  ),
                ),
              ),
              data: (tareas) {
                final filtradas = _aplicarFiltro(tareas);
                if (filtradas.isEmpty) {
                  return RefreshIndicator(
                    onRefresh: () => ref.read(tareasProvider.notifier).refrescar(),
                    child: ListView(
                      children: [
                        const SizedBox(height: 80),
                        const Icon(Icons.check_circle_outline,
                            size: 56, color: colorSecundarioTexto),
                        const SizedBox(height: 12),
                        Text(
                          _filtro == 'todas'
                              ? 'No tienes tareas todavía'
                              : 'Sin tareas en "${etiquetaEstado(_filtro)}"',
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: colorSecundarioTexto),
                        ),
                      ],
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () => ref.read(tareasProvider.notifier).refrescar(),
                  child: ListView.separated(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(16, 4, 16, 88),
                    itemCount: filtradas.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (contexto, indice) => _tarjeta(filtradas[indice]),
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

class _FiltroChip extends StatelessWidget {
  const _FiltroChip({
    required this.texto,
    required this.activo,
    required this.onTap,
    this.color,
  });

  final String texto;
  final bool activo;
  final VoidCallback onTap;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final tono = color ?? colorOrbitAcento;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text(texto),
        selected: activo,
        onSelected: (_) => onTap(),
        selectedColor: tono.withValues(alpha: 0.18),
        labelStyle: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: activo ? tono : colorSecundarioTexto,
        ),
        side: BorderSide(color: activo ? tono : const Color(0xFF334155)),
      ),
    );
  }
}
