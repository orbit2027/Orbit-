class Usuario {
  final String id;
  final String nombreCompleto;
  final String correo;
  final String rol;
  final String? fechaRegistro;

  const Usuario({
    required this.id,
    required this.nombreCompleto,
    required this.correo,
    required this.rol,
    this.fechaRegistro,
  });

  factory Usuario.desdeJson(Map<String, dynamic> json) {
    return Usuario(
      id: json['id'] as String? ?? '',
      nombreCompleto: json['nombre_completo'] as String? ?? '',
      correo: json['correo'] as String? ?? '',
      rol: json['rol'] as String? ?? 'usuario',
      fechaRegistro: json['fecha_registro'] as String?,
    );
  }

  String get iniciales {
    final partes = nombreCompleto.trim().split(RegExp(r'\s+'));
    if (partes.isEmpty || partes.first.isEmpty) return '?';
    if (partes.length == 1) return partes.first[0].toUpperCase();
    return (partes.first[0] + partes.last[0]).toUpperCase();
  }
}
