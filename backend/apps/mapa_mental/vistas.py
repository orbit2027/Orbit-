"""
Vistas API para el módulo de mapa mental.
Implementa nodos, conexiones y conversión a tarea (RF-MAP-06).
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .modelo import NodoMapa, ConexionNodo
from .serializador import NodoMapaSerializador, ConexionNodoSerializador
from apps.tareas.modelo import Tarea


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mapa_completo(request):
    """
    RF-MAP-05: Retorna el mapa mental completo del usuario.
    Incluye todos los nodos y conexiones.
    """
    nodos = NodoMapa.objects.filter(usuario=request.user)
    conexiones = ConexionNodo.objects.filter(usuario=request.user)

    return Response({
        'nodos': NodoMapaSerializador(nodos, many=True).data,
        'conexiones': ConexionNodoSerializador(conexiones, many=True).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_nodo(request):
    """RF-MAP-01: Crear un nuevo nodo en el mapa mental."""
    serializador = NodoMapaSerializador(data=request.data)
    if serializador.is_valid():
        serializador.save(usuario=request.user)
        return Response(
            serializador.data,
            status=status.HTTP_201_CREATED
        )
    return Response(
        serializador.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def detalle_nodo(request, nodo_id):
    """
    RF-MAP-03/04: Editar o eliminar un nodo.
    PATCH actualiza texto/color/posición, DELETE elimina nodo y sus conexiones.
    """
    try:
        nodo = NodoMapa.objects.get(id=nodo_id, usuario=request.user)
    except NodoMapa.DoesNotExist:
        return Response(
            {'error': 'Nodo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'PATCH':
        serializador = NodoMapaSerializador(
            nodo, data=request.data, partial=True
        )
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data, status=status.HTTP_200_OK)
        return Response(
            serializador.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        # RF-MAP-04: Las conexiones asociadas se eliminan por FK CASCADE
        nodo.delete()
        return Response(
            {'mensaje': 'Nodo y conexiones eliminados'},
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crearConexion(request):
    """RF-MAP-02: Crear una conexión visual entre dos nodos."""
    serializador = ConexionNodoSerializador(data=request.data)
    if serializador.is_valid():
        serializador.save(usuario=request.user)
        return Response(
            serializador.data,
            status=status.HTTP_201_CREATED
        )
    return Response(
        serializador.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminarConexion(request, conexion_id):
    """Eliminar una conexión entre nodos."""
    try:
        conexion = ConexionNodo.objects.get(
            id=conexion_id, usuario=request.user
        )
        conexion.delete()
        return Response(
            {'mensaje': 'Conexión eliminada'},
            status=status.HTTP_200_OK
        )
    except ConexionNodo.DoesNotExist:
        return Response(
            {'error': 'Conexión no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convertir_nodo_en_tarea(request, nodo_id):
    """
    RF-MAP-06: Convertir un nodo en tarea del tablero Kanban.
    El nodo queda marcado como convertido y la tarea hereda su texto.
    Acepta campos opcionales (descripcion, etiqueta, fecha_limite)
    capturados en el modal de conversión del frontend.
    """
    try:
        nodo = NodoMapa.objects.get(id=nodo_id, usuario=request.user)
    except NodoMapa.DoesNotExist:
        return Response(
            {'error': 'Nodo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if nodo.convertido_en_tarea:
        return Response(
            {'error': 'Este nodo ya fue convertido en tarea'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Crear tarea heredando el texto del nodo como título
    tarea = Tarea(
        titulo=nodo.texto,
        descripcion=request.data.get('descripcion', ''),
        estado='por_hacer',
        usuario=request.user,
        origen_nodo=str(nodo.id),
        color_etiqueta=nodo.color
    )

    # Campos adicionales opcionales del modal de conversión
    if request.data.get('etiqueta'):
        tarea.etiqueta = request.data['etiqueta']
    if request.data.get('color_etiqueta'):
        tarea.color_etiqueta = request.data['color_etiqueta']
    if request.data.get('fecha_limite'):
        tarea.fecha_limite = request.data['fecha_limite']

    tarea.save()

    # Marcar nodo como convertido
    nodo.convertido_en_tarea = True
    nodo.id_tarea_generada = str(tarea.id)
    nodo.save()

    return Response({
        'mensaje': 'Nodo convertido en tarea exitosamente',
        'tarea_id': str(tarea.id)
    }, status=status.HTTP_201_CREATED)
