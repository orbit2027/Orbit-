import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../datos/modelos/proyecto.dart';
import '../estado/proyectos_controlador.dart';
import '../nucleo/tema.dart';
import 'proyectos.dart' show parsearColorHex;

class EditorProyectoPantalla extends ConsumerStatefulWidget {
  const EditorProyectoPantalla({super.key, this.proyecto});

  final Proyecto? proyecto;

  @override
  ConsumerState<EditorProyectoPantalla> createState() => _EditorProyectoPantallaState();
}

class _EditorProyectoPantallaState extends ConsumerState<EditorProyectoPantalla> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nombreCtrl;
  late final TextEditingController _descripcionCtrl;

  late String _colorHex;
  DateTime? _fechaLimite;
  bool _guardando = false;

  bool get _esEdicion => widget.proyecto != null;

  @override
  void initState() {
    super.initState();
    final proyecto = widget.proyecto;
    _nombreCtrl = TextEditingController(text: proyecto?.nombre ?? '');
    _descripcionCtrl = TextEditingController(text: proyecto?.descripcion ?? '');
    _colorHex = proyecto?.color ?? '#00E5FF';
    if (proyecto?.fechaLimite != null) {
      _fechaLimite = DateTime.tryParse(proyecto!.fechaLimite!);
    }
  }

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _descripcionCtrl.dispose();
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

  Future<void> _guardar() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    FocusScope.of(context).unfocus();
    setState(() => _guardando = true);

    final datos = <String, dynamic>{
      'nombre': _nombreCtrl.text.trim(),
      'descripcion': _descripcionCtrl.text.trim(),
      'color': _colorHex,
      'fecha_limite': _fechaLimite == null
          ? null
          : '${_fechaLimite!.year.toString().padLeft(4, '0')}-'
              '${_fechaLimite!.month.toString().padLeft(2, '0')}-'
              '${_fechaLimite!.day.toString().padLeft(2, '0')}',
    };

    try {
      if (_esEdicion) {
        await ref
            .read(proyectosProvider.notifier)
            .actualizar(widget.proyecto!.id, datos);
      } else {
        await ref.read(proyectosProvider.notifier).crear(datos);
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

  @override
  Widget build(BuildContext context) {
    final opcionesColor = <_OpcionColor>[
      const _OpcionColor('#00E5FF', 'Cian'),
      const _OpcionColor('#F59E0B', 'Ámbar'),
      const _OpcionColor('#A78BFA', 'Violeta'),
      const _OpcionColor('#00C48C', 'Verde'),
      const _OpcionColor('#FF4D4D', 'Rojo'),
      const _OpcionColor('#F472B6', 'Rosa'),
      const _OpcionColor('#38BDF8', 'Celeste'),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(_esEdicion ? 'Editar proyecto' : 'Nuevo proyecto'),
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              TextFormField(
                controller: _nombreCtrl,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(
                  labelText: 'Nombre *',
                  prefixIcon: Icon(Icons.folder_outlined),
                ),
                validator: (valor) {
                  final nombre = valor?.trim() ?? '';
                  if (nombre.isEmpty) return 'Ingresa un nombre';
                  if (nombre.length < 3) return 'Nombre demasiado corto';
                  if (nombre.length > 100) return 'Máximo 100 caracteres';
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
              const SizedBox(height: 20),
              Text('Color', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final opcion in opcionesColor)
                    _MuestradorColor(
                      color: parsearColorHex(opcion.hex),
                      nombre: opcion.nombre,
                      seleccionado: _colorHex.toUpperCase() == opcion.hex,
                      onTap: () => setState(() => _colorHex = opcion.hex),
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
                      onPressed: () => setState(() => _fechaLimite = null),
                    ),
                ],
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
                    : Text(_esEdicion ? 'Guardar cambios' : 'Crear proyecto'),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: _guardando ? null : () => Navigator.of(context).pop(false),
                child: const Text('Cancelar'),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}

class _OpcionColor {
  const _OpcionColor(this.hex, this.nombre);

  final String hex;
  final String nombre;
}

class _MuestradorColor extends StatelessWidget {
  const _MuestradorColor({
    required this.color,
    required this.nombre,
    required this.seleccionado,
    required this.onTap,
  });

  final Color color;
  final String nombre;
  final bool seleccionado;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: seleccionado ? 0.22 : 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: seleccionado ? color : const Color(0xFF334155),
            width: seleccionado ? 2 : 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              height: 16,
              width: 16,
              decoration: BoxDecoration(color: color, shape: BoxShape.circle),
            ),
            const SizedBox(width: 6),
            Text(
              nombre,
              style: TextStyle(
                fontSize: 13,
                fontWeight: seleccionado ? FontWeight.w700 : FontWeight.w400,
                color: seleccionado ? color : colorSecundarioTexto,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
