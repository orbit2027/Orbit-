import 'package:flutter/material.dart';

const Color colorOrbitFondo = Color(0xFF0A192F);
const Color colorOrbitSuperficie = Color(0xFF112240);
const Color colorOrbitAcento = Color(0xFF00E5FF);
const Color colorOrbitTexto = Color(0xFFE2E8F0);
const Color colorOrbitError = Color(0xFFFF4D4D);
const Color colorSecundarioTexto = Color(0xFF94A3B8);
const Color colorOrbitExito = Color(0xFF00C48C);
const Color colorOrbitAdvertencia = Color(0xFFF59E0B);

const Map<String, Color> coloresEtiqueta = {
  'Urgente': colorOrbitError,
  'Personal': Color(0xFFA78BFA),
  'Trabajo': colorOrbitAcento,
  'Estudio': colorOrbitAdvertencia,
  'Hogar': colorOrbitExito,
};

final ThemeData temaOrbit = ThemeData(
  useMaterial3: true,
  brightness: Brightness.dark,
  colorScheme: const ColorScheme.dark(
    primary: colorOrbitAcento,
    secondary: Color(0xFFA78BFA),
    surface: colorOrbitFondo,
    onSurface: colorOrbitTexto,
    error: colorOrbitError,
    outline: Color(0x4D64748B),
  ),
  scaffoldBackgroundColor: colorOrbitFondo,
  appBarTheme: const AppBarTheme(
    backgroundColor: colorOrbitFondo,
    surfaceTintColor: Colors.transparent,
    elevation: 0,
    centerTitle: false,
  ),
  cardTheme: const CardThemeData(
    color: colorOrbitSuperficie,
    surfaceTintColor: Colors.transparent,
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(16)),
    ),
  ),
  inputDecorationTheme: InputDecorationThemeData(
    filled: true,
    fillColor: colorOrbitSuperficie,
    hintStyle: const TextStyle(color: Color(0xFF64748B)),
    labelStyle: const TextStyle(color: colorOrbitTexto),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: colorOrbitAcento, width: 1.5),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: colorOrbitError),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: colorOrbitError, width: 1.5),
    ),
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
  ),
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: colorOrbitAcento,
      foregroundColor: colorOrbitFondo,
      minimumSize: const Size.fromHeight(52),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      textStyle: const TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w700,
      ),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: colorOrbitAcento,
      minimumSize: const Size.fromHeight(52),
      side: const BorderSide(color: colorOrbitAcento),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
  ),
  floatingActionButtonTheme: const FloatingActionButtonThemeData(
    backgroundColor: colorOrbitAcento,
    foregroundColor: colorOrbitFondo,
  ),
  navigationBarTheme: NavigationBarThemeData(
    backgroundColor: colorOrbitSuperficie,
    indicatorColor: colorOrbitAcento.withValues(alpha: 0.18),
    height: 68,
    labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
  ),
  chipTheme: ChipThemeData(
    backgroundColor: colorOrbitSuperficie,
    selectedColor: colorOrbitAcento.withValues(alpha: 0.25),
    side: BorderSide.none,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(999),
    ),
  ),
  snackBarTheme: SnackBarThemeData(
    backgroundColor: colorOrbitSuperficie,
    contentTextStyle: const TextStyle(color: colorOrbitTexto),
    behavior: SnackBarBehavior.floating,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
    ),
  ),
  dialogTheme: const DialogThemeData(
    backgroundColor: colorOrbitSuperficie,
    surfaceTintColor: Colors.transparent,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(20)),
    ),
  ),
  dividerTheme: const DividerThemeData(
    color: Color(0x3364748B),
    thickness: 1,
  ),
);
