import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:orbit_movil/nucleo/tema.dart';
import 'package:orbit_movil/pantallas/login.dart';

void main() {
  testWidgets('el login muestra sus campos', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(theme: temaOrbit, home: const LoginPantalla()),
      ),
    );

    expect(find.text('Correo electrónico'), findsOneWidget);
    expect(find.text('Contraseña'), findsOneWidget);
    expect(find.text('Iniciar sesión'), findsOneWidget);
    expect(find.text('¿No tienes cuenta? Regístrate'), findsOneWidget);
    expect(find.byIcon(Icons.rocket_launch_outlined), findsOneWidget);
  });

  testWidgets('valida el formulario vacío al enviar', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(theme: temaOrbit, home: const LoginPantalla()),
      ),
    );

    final boton = find.widgetWithText(ElevatedButton, 'Iniciar sesión');
    await tester.ensureVisible(boton);
    await tester.tap(boton);
    await tester.pump();

    expect(find.text('Ingresa tu correo'), findsOneWidget);
    expect(find.text('Ingresa tu contraseña'), findsOneWidget);
  });

  testWidgets('rechaza un correo inválido', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(theme: temaOrbit, home: const LoginPantalla()),
      ),
    );

    await tester.enterText(find.byType(TextFormField).first, 'no-es-correo');
    final boton = find.widgetWithText(ElevatedButton, 'Iniciar sesión');
    await tester.ensureVisible(boton);
    await tester.tap(boton);
    await tester.pump();

    expect(find.text('Ingresa un correo válido'), findsOneWidget);
  });
}
