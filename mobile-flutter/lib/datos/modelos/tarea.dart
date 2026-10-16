class Tarea {
  static const String porHacer = 'por_hacer';
  static const String enProgreso = 'en_progreso';
  static const String completado = 'completado';

  static const List<String> estados = [porHacer, enProgreso, completado];

  final String id;
  final String titulo;
  final String descripcion;
  final String estado;
  final String etiqueta;
  final String colorEtiqueta;
  final String? fechaLimite;
  final String origenNodo;
  final String proyecto;
  final String usuario;
  final String? fechaCreacion;

  const Tarea({
    required this.id,
    required this.titulo,
    required this.descripcion,
    required this.estado,
    required this.etiqueta,
    required this.colorEtiqueta,
    this.fechaLimite,
    required this.origenNodo,
    required this.proyecto,
    required this.usuario,
    this.fechaCreacion,
  });

  factory Tarea.desdeJson(Map<String, dynamic> json) {
    return Tarea(
      id: json['id'] as String? ?? '',
      titulo: json['titulo'] as String? ?? '',
      descripcion: json['descripcion'] as String? ?? '',
      estado: json['estado'] as String? ?? porHacer,
      etiqueta: json['etiqueta'] as String? ?? '',
      colorEtiqueta: json['color_etiqueta'] as String? ?? '#00E5FF',
      fechaLimite: json['fecha_limite'] as String?,
      origenNodo: json['origen_nodo'] as String? ?? '',
      proyecto: json['proyecto'] as String? ?? '',
      usuario: json['usuario'] as String? ?? '',
      fechaCreacion: json['fecha_creacion'] as String?,
    );
  }

  Tarea copiarCon({
    String? id,
    String? titulo,
    String? descripcion,
    String? estado,
    String? etiqueta,
    String? colorEtiqueta,
    String? fechaLimite,
    String? origenNodo,
    String? proyecto,
    String? usuario,
    String? fechaCreacion,
  }) {
    return Tarea(
      id: id ?? this.id,
      titulo: titulo ?? this.titulo,
      descripcion: descripcion ?? this.descripcion,
      estado: estado ?? this.estado,
      etiqueta: etiqueta ?? this.etiqueta,
      colorEtiqueta: colorEtiqueta ?? this.colorEtiqueta,
      fechaLimite: fechaLimite ?? this.fechaLimite,
      origenNodo: origenNodo ?? this.origenNodo,
      proyecto: proyecto ?? this.proyecto,
      usuario: usuario ?? this.usuario,
      fechaCreacion: fechaCreacion ?? this.fechaCreacion,
    );
  }

  String get etiquetaEstado {
    switch (estado) {
      case enProgreso:
        return 'En progreso';
      case completado:
        return 'Completado';
      default:
        return 'Por hacer';
    }
  }
}
