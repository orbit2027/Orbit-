"""
Vistas API para el módulo de mapa mental.
Implementa nodos, conexiones y conversión a tarea (RF-MAP-06).
"""
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer

from .modelo import NodoMapa, ConexionNodo
from .serializador import (
    NodoMapaSerializador,
    ConexionNodoSerializador,
    MapaCompletoSerializador,
    ConvertirNodoSerializador,
    ConvertirNodoRespuestaSerializador,
    ConvertirSeleccionSerializador,
    ConvertirSeleccionRespuestaSerializador,
)
from apps.tareas.modelo import Tarea

MensajeSerializador = inline_serializer(
    name='MapaMensaje', fields={'mensaje': serializers.CharField()}
)


def _crear_tarea_desde_nodo(nodo, datos):
    """Crea una tarea Kanban a partir de un nodo (RF-MAP-06)."""
    tarea = Tarea(
        titulo=nodo.texto,
        descripcion=datos.get('descripcion', ''),
        estado='por_hacer',
        usuario=nodo.usuario,
        origen_nodo=str(nodo.id),
        color_etiqueta=nodo.color
    )
    if datos.get('etiqueta'):
        tarea.etiqueta = datos['etiqueta']
    if datos.get('color_etiqueta'):
        tarea.color_etiqueta = datos['color_etiqueta']
    if datos.get('fecha_limite'):
        tarea.fecha_limite = datos['fecha_limite']
    tarea.save()

    nodo.convertido_en_tarea = True
    nodo.id_tarea_generada = str(tarea.id)
    nodo.save()
    return tarea

@extend_schema(
    tags=['Mapa mental'],
    summary='Obtener el mapa mental completo',
    description='RF-MAP-05. Devuelve todos los nodos y conexiones del usuario.',
    responses={200: MapaCompletoSerializador},
)
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


@extend_schema(
    tags=['Mapa mental'],
    summary='Crear nodo',
    description='RF-MAP-01. Crea un nuevo nodo en el mapa mental.',
    request=NodoMapaSerializador,
    responses={201: NodoMapaSerializador, 400: None},
)
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

@extend_schema(
    tags=['Mapa mental'],
    summary='Editar nodo',
    description='RF-MAP-03. Actualiza texto, color y posición del nodo.',
    request=NodoMapaSerializador,
    responses={200: NodoMapaSerializador, 400: None, 404: None},
)
@extend_schema(
    tags=['Mapa mental'],
    summary='Eliminar nodo',
    description='RF-MAP-04. Elimina el nodo y sus conexiones asociadas.',
    responses={200: MensajeSerializador, 404: None},
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
        # Las conexiones asociadas se eliminan por FK CASCADE
        nodo.delete()
        return Response(
            {'mensaje': 'Nodo y conexiones eliminados'},
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=['Mapa mental'],
    summary='Crear conexión',
    description='RF-MAP-02. Crea una conexión visual entre dos nodos.',
    request=ConexionNodoSerializador,
    responses={201: ConexionNodoSerializador, 400: None},
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

@extend_schema(
    tags=['Mapa mental'],
    summary='Eliminar conexión',
    request=None,
    responses={200: MensajeSerializador, 404: None},
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


@extend_schema(
    tags=['Mapa mental'],
    summary='Convertir nodo en tarea',
    description='RF-MAP-06. Crea una tarea a partir del nodo y lo marca como convertido.',
    request=ConvertirNodoSerializador,
    responses={201: ConvertirNodoRespuestaSerializador, 400: None, 404: None},
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

    tarea = _crear_tarea_desde_nodo(nodo, request.data)

    return Response({
        'mensaje': 'Nodo convertido en tarea exitosamente',
        'tarea_id': str(tarea.id)
    }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Mapa mental'],
    summary='Convertir nodos seleccionados en tareas',
    description='RF-MAP-07. Convierte una selección de nodos en tareas del '
                'tablero Kanban de una sola vez.',
    request=ConvertirSeleccionSerializador,
    responses={201: ConvertirSeleccionRespuestaSerializador, 400: None},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convertir_seleccion_en_tareas(request):
    """
    RF-MAP-07: Convierte todas las ideas seleccionadas en tareas.
    Cada nodo convertido queda marcado; los ya convertidos o ajenos
    se listan como omitidos sin abortar el lote.
    """
    serializador = ConvertirSeleccionSerializador(data=request.data)
    if not serializador.is_valid():
        return Response(
            serializador.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    datos = serializador.validated_data
    ids_solicitados = datos['nodos']

    nodos = NodoMapa.objects.filter(
        id__in=ids_solicitados, usuario=request.user
    )
    por_id = {str(nodo.id): nodo for nodo in nodos}

    creadas = []
    omitidas = []
    nodos_convertidos = []
    for nodo_id in ids_solicitados:
        nodo = por_id.get(nodo_id)
        if not nodo or nodo.convertido_en_tarea:
            omitidas.append(nodo_id)
            continue
        tarea = _crear_tarea_desde_nodo(nodo, datos)
        creadas.append(str(tarea.id))
        nodos_convertidos.append(nodo_id)

    if creadas:
        mensaje = f'{len(creadas)} tarea(s) creada(s) desde el mapa mental'
    else:
        mensaje = 'No se crearon tareas: los nodos seleccionados ya fueron convertidos'

    return Response({
        'mensaje': mensaje,
        'creadas': creadas,
        'omitidas': omitidas,
        'nodos_convertidos': nodos_convertidos,
    }, status=status.HTTP_201_CREATED)