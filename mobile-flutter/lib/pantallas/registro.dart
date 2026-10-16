import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../estado/auth_controlador.dart';
import '../nucleo/tema.dart';

class RegistroPantalla extends ConsumerStatefulWidget {
  const RegistroPantalla({super.key});

  @override
  ConsumerState<RegistroPantalla> createState() => _RegistroPantallaState();
}

class _RegistroPantallaState extends ConsumerState<RegistroPantalla> {
  final _formKey = GlobalKey<FormState>();
  final _nombreCtrl = TextEditingController();
  final _correoCtrl = TextEditingController();
  final _claveCtrl = TextEditingController();
  final _claveConfirmadaCtrl = TextEditingController();
  bool _verClave = false;

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _correoCtrl.dispose();
    _claveCtrl.dispose();
    _claveConfirmadaCtrl.dispose();
    super.dispose();
  }

  Future<void> _enviar() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    FocusScope.of(context).unfocus();
    await ref.read(authProvider.notifier).registrar(
          nombreCompleto: _nombreCtrl.text.trim(),
          correo: _correoCtrl.text.trim(),
          contrasena: _claveCtrl.text,
        );
    if (mounted && ref.read(authProvider).autenticado) {
      Navigator.of(context).pop();
    }
  }

  String? _validarClave(String? valor) {
    final clave = valor ?? '';
    if (clave.isEmpty) return 'Crea una contraseña';
    if (clave.length < 8) return 'Mínimo 8 caracteres';
    if (!RegExp(r'[A-Z]').hasMatch(clave)) return 'Incluye una mayúscula';
    if (!RegExp(r'\d').hasMatch(clave)) return 'Incluye un número';
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final estado = ref.watch(authProvider);

    ref.listen(authProvider, (anterior, actual) {
      final error = actual.error;
      if (error != null && error != anterior?.error && mounted) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(content: Text(error)));
      }
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Crear cuenta')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  TextFormField(
                    controller: _nombreCtrl,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(
                      labelText: 'Nombre completo',
                      prefixIcon: Icon(Icons.person_outline),
                    ),
                    validator: (valor) {
                      final nombre = valor?.trim() ?? '';
                      if (nombre.isEmpty) return 'Ingresa tu nombre';
                      if (nombre.length < 3) return 'Nombre demasiado corto';
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _correoCtrl,
                    keyboardType: TextInputType.emailAddress,
                    decoration: const InputDecoration(
                      labelText: 'Correo electrónico',
                      prefixIcon: Icon(Icons.mail_outline),
                    ),
                    validator: (valor) {
                      final correo = valor?.trim() ?? '';
                      if (correo.isEmpty) return 'Ingresa tu correo';
                      final valido = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
                          .hasMatch(correo);
                      return valido ? null : 'Ingresa un correo válido';
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _claveCtrl,
                    obscureText: !_verClave,
                    decoration: InputDecoration(
                      labelText: 'Contraseña',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(
                          _verClave ? Icons.visibility_off : Icons.visibility,
                        ),
                        onPressed: () => setState(() => _verClave = !_verClave),
                      ),
                      helperText: 'Mínimo 8, una mayúscula y un número',
                      helperMaxLines: 2,
                    ),
                    validator: _validarClave,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _claveConfirmadaCtrl,
                    obscureText: !_verClave,
                    decoration: const InputDecoration(
                      labelText: 'Confirmar contraseña',
                      prefixIcon: Icon(Icons.lock_reset_outlined),
                    ),
                    validator: (valor) =>
                        valor != _claveCtrl.text ? 'Las contraseñas no coinciden' : null,
                    onFieldSubmitted: (_) => _enviar(),
                  ),
                  const SizedBox(height: 28),
                  ElevatedButton(
                    onPressed: estado.enviando ? null : _enviar,
                    child: estado.enviando
                        ? const SizedBox(
                            height: 22,
                            width: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: colorOrbitFondo,
                            ),
                          )
                        : const Text('Crear cuenta'),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: estado.enviando ? null : () => Navigator.of(context).pop(),
                    child: const Text('Ya tengo una cuenta'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
