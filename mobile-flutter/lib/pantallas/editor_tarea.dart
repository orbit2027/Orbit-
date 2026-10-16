import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../datos/modelos/tarea.dart';
import '../estado/proyectos_controlador.dart';
import '../estado/tareas_controlador.dart';
import '../nucleo/tema.dart';
import 'tareas.dart' show estadosTarea, etiquetaEstado, colorEstado;

class EditorTareaPantalla extends ConsumerStatefulWidget {
  const EditorTareaPantalla({super.key, this.tarea});

  final Tarea? tarea;

  @override
  ConsumerState<EditorTareaPantalla> createState() => _EditorTareaPantallaState();
}

class _EditorTareaPantallaState extends ConsumerState<EditorTareaPantalla> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _tituloCtrl;
  late final TextEditingController _descripcionCtrl;
  late final TextEditingController _etiquetaCtrl;

  String _estado = 'por_hacer';
  DateTime? _fechaLimite;
  String _proyectoId = '';
  bool _guardando = false;

  bool get _esEdicion => widget.tarea != null;

  @override
  void initState() {
    super.initState();
    final tarea = widget.tarea;
    _tituloCtrl = TextEditingController(text: tarea?.titulo ?? '');
    _descripcionCtrl = TextEditingController(text: tarea?.descripcion ?? '');
    _etiquetaCtrl = TextEditingController(text: tarea?.etiqueta ?? '');
    _estado = estadosTarea.contains(tarea?.estado) ? tarea!.estado : 'por_hacer';
    _proyectoId = tarea?.proyecto ?? '';
    if (tarea?.fechaLimite != null) {
      _fechaLimite = DateTime.tryParse(tarea!.fechaLimite!);
    }
  }

  @override
  void dispose() {
    _tituloCtrl.dispose();
    _descripcionCtrl.dispose();
    _etiquetaCtrl.dispose();
    super.dispose();
  }

  Future<void> _elegirFecha() async {
    final hoy = DateTime.now();
    final elegida = await showDatePicker(
      context: context,
      initialDate: _fechaLimite ?? hoy,
      firstDate: DateTime(hoy.year - 2),
      lastDate: DateTime(hoy.year + 5),
    );
    if (elegida != null) {
      setState(() => _fechaLimite = elegida);
    }
  }

  void _limpiarFecha() => setState(() => _fechaLimite = null);

  Future<void> _guardar() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    FocusScope.of(context).unfocus();
    setState(() => _guardando = true);

    final datos = <String, dynamic>{
      'titulo': _tituloCtrl.text.trim(),
      'descripcion': _descripcionCtrl.text.trim(),
      'etiqueta': _etiquetaCtrl.text.trim(),
      'estado': _estado,
      'fecha_limite': _fechaLimite == null
          ? null
          : '${_fechaLimite!.year.toString().padLeft(4, '0')}-'
              '${_fechaLimite!.month.toString().padLeft(2, '0')}-'
              '${_fechaLimite!.day.toString().padLeft(2, '0')}',
      'proyecto': _proyectoId.isEmpty ? null : _proyectoId,
    };

    try {
      if (_esEdicion) {
        await ref.read(tareasProvider.notifier).actualizar(widget.tarea!.id, datos);
      } else {
        await ref.read(tareasProvider.notifier).crear(datos);
      }
      if (mounted) Navigator.of(context).pop(true);
    } catch (error) {
      if (mounted) {
        setState(() => _guardando = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.toString())),
        );
      }
    }
  }

  Future<void> _eliminar() async {
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: const Text('Eliminar tarea'),
        content: Text('¿Eliminar "${widget.tarea!.titulo}"?'),
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
        await ref.read(tareasProvider.notifier).eliminar(widget.tarea!.id);
        if (mounted) Navigator.of(context).pop(true);
      } catch (error) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(error.toString())),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final proyectosAsync = ref.watch(proyectosProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(_esEdicion ? 'Editar tarea' : 'Nueva tarea'),
        actions: [
          if (_esEdicion)
            IconButton(
              icon: const Icon(Icons.delete_outline, color: colorOrbitError),
              onPressed: _guardando ? null : _eliminar,
            ),
        ],
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              TextFormField(
                controller: _tituloCtrl,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(
                  labelText: 'Título *',
                  prefixIcon: Icon(Icons.title),
                ),
                validator: (valor) {
                  final titulo = valor?.trim() ?? '';
                  if (titulo.isEmpty) return 'Ingresa un título';
                  if (titulo.length < 3) return 'Título demasiado corto';
                  if (titulo.length > 200) return 'Máximo 200 caracteres';
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _descripcionCtrl,
                textCapitalization: TextCapitalization.sentences,
                maxLines: 4,
                minLines: 2,
                decoration: const InputDecoration(
                  labelText: 'Descripción',
                  alignLabelWithHint: true,
                  prefixIcon: Icon(Icons.notes),
                ),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _etiquetaCtrl,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Etiqueta',
                  hintText: 'ej. Diseño, Backend, Personal',
                  prefixIcon: Icon(Icons.label_outline),
                ),
              ),
              const SizedBox(height: 20),
              Text('Estado', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [
                  for (final estado in estadosTarea)
                    ChoiceChip(
                      label: Text(etiquetaEstado(estado)),
                      selected: _estado == estado,
                      onSelected: (_) => setState(() => _estado = estado),
                      selectedColor: colorEstado(estado).withValues(alpha: 0.18),
                      labelStyle: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: _estado == estado
                            ? colorEstado(estado)
                            : colorSecundarioTexto,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 20),
              Text('Fecha límite', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _elegirFecha,
                      icon: const Icon(Icons.event),
                      label: Text(
                        _fechaLimite == null
                            ? 'Sin fecha'
                            : '${_fechaLimite!.day.toString().padLeft(2, '0')}/'
                                '${_fechaLimite!.month.toString().padLeft(2, '0')}/'
                                '${_fechaLimite!.year}',
                      ),
                    ),
                  ),
                  if (_fechaLimite != null)
                    IconButton(
                      icon: const Icon(Icons.clear),
                      tooltip: 'Quitar fecha',
                      onPressed: _limpiarFecha,
                    ),
                ],
              ),
              const SizedBox(height: 20),
              Text('Proyecto', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              proyectosAsync.when(
                loading: () => const LinearProgressIndicator(),
                error: (_, _) => const Text(
                  'No se pudieron cargar los proyectos',
                  style: TextStyle(color: colorSecundarioTexto),
                ),
                data: (proyectos) {
                  final activos =
                      proyectos.where((p) => !p.estaArchivado).toList();
                  final ids = activos.map((p) => p.id).toSet();
                  if (_proyectoId.isNotEmpty && !ids.contains(_proyectoId)) {
                    _proyectoId = '';
                  }
                  return DropdownButtonFormField<String>(
                    initialValue: _proyectoId.isEmpty ? null : _proyectoId,
                    decoration: const InputDecoration(
                      hintText: 'Sin proyecto',
                      prefixIcon: Icon(Icons.folder_outlined),
                    ),
                    items: [
                      const DropdownMenuItem<String>(
                        value: '',
                        child: Text('Sin proyecto'),
                      ),
                      for (final proyecto in activos)
                        DropdownMenuItem<String>(
                          value: proyecto.id,
                          child: Text(proyecto.nombre),
                        ),
                    ],
                    onChanged: (valor) => setState(() => _proyectoId = valor ?? ''),
                  );
                },
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: _guardando ? null : _guardar,
                child: _guardando
                    ? const SizedBox(
                        height: 22,
                        width: 22,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          color: colorOrbitFondo,
                        ),
                      )
                    : Text(_esEdicion ? 'Guardar cambios' : 'Crear tarea'),
              ),
              if (_esEdicion) ...[
                const SizedBox(height: 8),
                TextButton(
                  onPressed: _guardando ? null : () => Navigator.of(context).pop(false),
                  child: const Text('Cancelar'),
                ),
              ],
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
