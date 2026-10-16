import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'estado/auth_controlador.dart';
import 'nucleo/tema.dart';
import 'pantallas/inicio.dart';
import 'pantallas/login.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: AplicacionOrbit()));
}

class AplicacionOrbit extends StatelessWidget {
  const AplicacionOrbit({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Orbit',
      debugShowCheckedModeBanner: false,
      theme: temaOrbit,
      home: const PuertaDeAcceso(),
    );
  }
}

class PuertaDeAcceso extends ConsumerStatefulWidget {
  const PuertaDeAcceso({super.key});

  @override
  ConsumerState<PuertaDeAcceso> createState() => _PuertaDeAccesoState();
}

class _PuertaDeAccesoState extends ConsumerState<PuertaDeAcceso> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(authProvider.notifier).restaurarSesion());
  }

  @override
  Widget build(BuildContext context) {
    final estado = ref.watch(authProvider);

    if (estado.comprobandoSesion) {
      return const _CargandoInicial();
    }
    if (estado.autenticado) {
      return const InicioPantalla();
    }
    return const LoginPantalla();
  }
}

class _CargandoInicial extends StatelessWidget {
  const _CargandoInicial();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.rocket_launch_outlined, size: 56, color: colorOrbitAcento),
            SizedBox(height: 20),
            CircularProgressIndicator(color: colorOrbitAcento),
          ],
        ),
      ),
    );
  }
}
