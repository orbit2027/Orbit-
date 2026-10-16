import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../estado/auth_controlador.dart';
import '../nucleo/tema.dart';

class PerfilPantalla extends ConsumerWidget {
  const PerfilPantalla({super.key});

  Future<void> _cerrarSesion(BuildContext context, WidgetRef ref) async {
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: const Text('Cerrar sesión'),
        content: const Text('¿Seguro que quieres cerrar sesión?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(contexto).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(contexto).pop(true),
            style: FilledButton.styleFrom(backgroundColor: colorOrbitError),
            child: const Text('Cerrar sesión'),
          ),
        ],
      ),
    );
    if (confirmado == true) {
      await ref.read(authProvider.notifier).cerrarSesion();
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final estado = ref.watch(authProvider);
    final usuario = estado.usuario;

    if (usuario == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Center(
            child: Container(
              height: 96,
              width: 96,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: colorOrbitAcento.withValues(alpha: 0.16),
                shape: BoxShape.circle,
                border: Border.all(color: colorOrbitAcento, width: 2),
              ),
              child: Text(
                usuario.iniciales,
                style: const TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.w800,
                  color: colorOrbitAcento,
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Center(
            child: Text(
              usuario.nombreCompleto,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
          const SizedBox(height: 4),
          Center(
            child: Chip(
              label: Text(
                usuario.rol == 'administrador' ? 'Administrador' : 'Usuario',
              ),
              avatar: Icon(
                usuario.rol == 'administrador'
                    ? Icons.verified_user_outlined
                    : Icons.person_outline,
                size: 18,
                color: colorOrbitAcento,
              ),
            ),
          ),
          const SizedBox(height: 32),
          Card(
            child: Column(
              children: [
                _Dato(icono: Icons.mail_outline, titulo: 'Correo', valor: usuario.correo),
                const Divider(height: 1, indent: 16, endIndent: 16),
                _Dato(
                  icono: Icons.calendar_today_outlined,
                  titulo: 'Miembro desde',
                  valor: usuario.fechaRegistro != null
                      ? _formatearFecha(usuario.fechaRegistro!)
                      : '—',
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () => _cerrarSesion(context, ref),
            icon: const Icon(Icons.logout),
            label: const Text('Cerrar sesión'),
            style: OutlinedButton.styleFrom(
              foregroundColor: colorOrbitError,
              side: const BorderSide(color: colorOrbitError),
            ),
          ),
        ],
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
}

class _Dato extends StatelessWidget {
  const _Dato({required this.icono, required this.titulo, required this.valor});

  final IconData icono;
  final String titulo;
  final String valor;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icono, color: colorOrbitAcento),
      title: Text(titulo, style: const TextStyle(fontSize: 13, color: Color(0xFF94A3B8))),
      subtitle: Text(valor, style: const TextStyle(fontSize: 15)),
    );
  }
}
