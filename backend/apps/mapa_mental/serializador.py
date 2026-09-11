"""
Serializadores DRF para el módulo de mapa mental.
Valida nodos, conexiones y conversión a tarea (RF-MAP-06).

Se usan `serializers.Serializer` simples (no ModelSerializer) porque
los documentos son de MongoEngine, no modelos del ORM de Django.
"""
from rest_framework import serializers
from .modelo import NodoMapa, ConexionNodo


class NodoMapaSerializador(serializers.Serializer):
    """Serializador para operaciones CRUD de nodos del mapa mental."""

    texto = serializers.CharField(max_length=200)
    color = serializers.CharField(max_length=7, required=False, default='#00E5FF')
    posicion_x = serializers.FloatField(required=False, default=0.0)
    posicion_y = serializers.FloatField(required=False, default=0.0)

    def validate_texto(self, valor):
        """Valida que el texto no esté vacío."""
        if not valor.strip():
            raise serializers.ValidationError(
                "El texto del nodo no puede estar vacío."
            )
        return valor.strip()

    def create(self, datos_validados):
        """Crea el documento de nodo en MongoDB."""
        nodo = NodoMapa(**datos_validados)
        nodo.save()
        return nodo

    def update(self, instancia, datos_validados):
        """Actualiza solo los campos enviados (texto/color/posición)."""
        for campo, valor in datos_validados.items():
            setattr(instancia, campo, valor)
        instancia.save()
        return instancia

    def to_representation(self, instancia):
        """Convierte el documento MongoEngine a JSON para el frontend."""
        return {
            'id': str(instancia.id),
            'texto': instancia.texto,
            'color': instancia.color,
            'posicion_x': instancia.posicion_x,
            'posicion_y': instancia.posicion_y,
            'convertido_en_tarea': bool(instancia.convertido_en_tarea),
            'id_tarea_generada': instancia.id_tarea_generada or '',
            'fecha_creacion': (
                instancia.fecha_creacion.isoformat()
                if instancia.fecha_creacion else None
            ),
        }


class ConexionNodoSerializador(serializers.Serializer):
    """
    Serializador para conexiones entre nodos.
    Recibe los IDs de los nodos como cadenas y resuelve las referencias.
    """

    nodo_origen = serializers.CharField()
    nodo_destino = serializers.CharField()

    def validate(self, attrs):
        """Valida que no se conecte un nodo consigo mismo."""
        if attrs['nodo_origen'] == attrs['nodo_destino']:
            raise serializers.ValidationError(
                "No se puede conectar un nodo consigo mismo."
            )
        return attrs

    def create(self, datos_validados):
        """Resuelve las referencias y crea la conexión."""
        try:
            origen = NodoMapa.objects.get(id=datos_validados['nodo_origen'])
            destino = NodoMapa.objects.get(id=datos_validados['nodo_destino'])
        except NodoMapa.DoesNotExist:
            raise serializers.ValidationError(
                "Uno de los nodos no existe o no es tuyo."
            )
        conexion = ConexionNodo(
            nodo_origen=origen,
            nodo_destino=destino,
            usuario=datos_validados['usuario'],
        )
        conexion.save()
        return conexion

    def to_representation(self, instancia):
        """Retorna los IDs de la conexión como cadenas."""
        return {
            'id': str(instancia.id),
            'nodo_origen': str(instancia.nodo_origen.id),
            'nodo_destino': str(instancia.nodo_destino.id),
        }
