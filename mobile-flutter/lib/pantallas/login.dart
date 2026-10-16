import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../estado/auth_controlador.dart';
import '../nucleo/tema.dart';
import 'registro.dart';

class LoginPantalla extends ConsumerStatefulWidget {
  const LoginPantalla({super.key});

  @override
  ConsumerState<LoginPantalla> createState() => _LoginPantallaState();
}

class _LoginPantallaState extends ConsumerState<LoginPantalla> {
  final _formKey = GlobalKey<FormState>();
  final _correoCtrl = TextEditingController();
  final _claveCtrl = TextEditingController();
  bool _verClave = false;

  @override
  void dispose() {
    _correoCtrl.dispose();
    _claveCtrl.dispose();
    super.dispose();
  }

  Future<void> _enviar() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    FocusScope.of(context).unfocus();
    await ref.read(authProvider.notifier).iniciarSesion(
          correo: _correoCtrl.text.trim(),
          contrasena: _claveCtrl.text,
        );
  }

  Future<void> _irARegistro() async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => const RegistroPantalla()),
    );
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
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const _MarcaOrbit(),
                  const SizedBox(height: 40),
                  TextFormField(
                    controller: _correoCtrl,
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const [AutofillHints.email],
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
                    autofillHints: const [AutofillHints.password],
                    decoration: InputDecoration(
                      labelText: 'Contraseña',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(
                          _verClave ? Icons.visibility_off : Icons.visibility,
                        ),
                        onPressed: () => setState(() => _verClave = !_verClave),
                      ),
                    ),
                    validator: (valor) =>
                        (valor == null || valor.isEmpty) ? 'Ingresa tu contraseña' : null,
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
                        : const Text('Iniciar sesión'),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: estado.enviando ? null : _irARegistro,
                    child: const Text('¿No tienes cuenta? Regístrate'),
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

class _MarcaOrbit extends StatelessWidget {
  const _MarcaOrbit();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          height: 84,
          width: 84,
          decoration: BoxDecoration(
            color: colorOrbitAcento.withValues(alpha: 0.14),
            shape: BoxShape.circle,
            border: Border.all(color: colorOrbitAcento, width: 2),
          ),
          child: const Icon(
            Icons.rocket_launch_outlined,
            size: 44,
            color: colorOrbitAcento,
          ),
        ),
        const SizedBox(height: 20),
        Text(
          'Orbit',
          style: Theme.of(context).textTheme.displaySmall?.copyWith(
                fontWeight: FontWeight.w800,
                color: colorOrbitTexto,
                letterSpacing: 1.2,
              ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Organiza tus ideas y tareas en órbita',
          textAlign: TextAlign.center,
          style: TextStyle(color: Color(0xFF94A3B8), fontSize: 14),
        ),
      ],
    );
  }
}
