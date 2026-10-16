class Proyecto {
  static const String activo = 'activo';
  static const String archivado = 'archivado';

  final String id;
  final String nombre;
  final String descripcion;
  final String color;
  final String estado;
  final String? fechaLimite;
  final String? fechaCreacion;
  final String usuario;
  final int tareasTotales;
  final int tareasCompletadas;
  final int tareasActivas;

  const Proyecto({
    required this.id,
    required this.nombre,
    required this.descripcion,
    required this.color,
    required this.estado,
    this.fechaLimite,
    this.fechaCreacion,
    required this.usuario,
    this.tareasTotales = 0,
    this.tareasCompletadas = 0,
    this.tareasActivas = 0,
  });

  factory Proyecto.desdeJson(Map<String, dynamic> json) {
    return Proyecto(
      id: json['id'] as String? ?? '',
      nombre: json['nombre'] as String? ?? '',
      descripcion: json['descripcion'] as String? ?? '',
      color: json['color'] as String? ?? '#00E5FF',
      estado: json['estado'] as String? ?? activo,
      fechaLimite: json['fecha_limite'] as String?,
      fechaCreacion: json['fecha_creacion'] as String?,
      usuario: json['usuario'] as String? ?? '',
      tareasTotales: (json['tareas_totales'] as num?)?.toInt() ?? 0,
      tareasCompletadas: (json['tareas_completadas'] as num?)?.toInt() ?? 0,
      tareasActivas: (json['tareas_activas'] as num?)?.toInt() ?? 0,
    );
  }

  bool get estaArchivado => estado == archivado;

  double get avance {
    if (tareasTotales == 0) return 0;
    return tareasCompletadas / tareasTotales;
  }
}
