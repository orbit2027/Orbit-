from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from drf_spectacular.utils import extend_schema, inline_serializer

from .modelo import Tarea
from .serializador import TareaSerializador, MoverTareaSerializador
from apps.comparticion.modelo import Comparticion
from apps.comparticion.permisos import nivel_sobre_tarea, puede_ver, puede_editar, puede_administrar

MensajeSerializador = inline_serializer(
    name='TareaMensaje', fields={'mensaje': serializers.CharField()}
)

@extend_schema(
    tags=['Tareas'],
    summary='Listar tareas',
    description='Propias + compartidas directamente + de proyectos compartidos.',
    responses={200: TareaSerializador(many=True)},
)
@extend_schema(
    tags=['Tareas'],
    summary='Crear tarea',
    request=TareaSerializador,
    responses={201: TareaSerializador, 400: None},
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def lista_tareas(request):
    if request.method == 'GET':
        # Propias + compartidas directamente + tareas de proyectos compartidos
        tareas_compartidas = Comparticion.objects.filter(
            compartido_con=request.user
        ).values_list('objeto_id', 'tipo_objeto')

        ids_tareas = [oid for oid, tipo in tareas_compartidas if tipo == 'tarea']
        proyectos_compartidos = [
            oid for oid, tipo in tareas_compartidas if tipo == 'proyecto'
        ]

        filtro = Q(usuario=request.user)
        if ids_tareas:
            filtro |= Q(id__in=ids_tareas)
        if proyectos_compartidos:
            filtro |= Q(proyecto__in=proyectos_compartidos)

        tareas = Tarea.objects.filter(filtro).order_by('-fecha_creacion')
        serializador = TareaSerializador(tareas, many=True)
        return Response(serializador.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializador = TareaSerializador(data=request.data)
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
    tags=['Tareas'],
    summary='Ver detalle de tarea',
    responses={200: TareaSerializador, 403: None, 404: None},
)
@extend_schema(
    tags=['Tareas'],
    summary='Editar tarea',
    request=TareaSerializador,
    responses={200: TareaSerializador, 400: None, 403: None, 404: None},
)
@extend_schema(
    tags=['Tareas'],
    summary='Eliminar tarea',
    responses={200: MensajeSerializador, 403: None, 404: None},
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def detalle_tarea(request, tarea_id):

    try:
        tarea = Tarea.objects.get(id=tarea_id)
    except Tarea.DoesNotExist:
        return Response(
            {'error': 'Tarea no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    nivel = nivel_sobre_tarea(request.user, tarea)

    if request.method == 'GET':
        if not puede_ver(nivel):
            return Response(
                {'error': 'No tienes acceso a esta tarea.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializador = TareaSerializador(tarea)
        return Response(serializador.data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        if not puede_editar(nivel):
            return Response(
                {'error': 'No tienes permisos para editar esta tarea.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializador = TareaSerializador(
            tarea, data=request.data, partial=(request.method == 'PATCH')
        )
        if serializador.is_valid():
            serializador.save()
            return Response(serializador.data, status=status.HTTP_200_OK)
        return Response(
            serializador.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        if not puede_administrar(nivel):
            return Response(
                {'error': 'No tienes permisos para eliminar esta tarea.'},
                status=status.HTTP_403_FORBIDDEN
            )
        tarea.delete()
        return Response(
            {'mensaje': 'Tarea eliminada'},
            status=status.HTTP_200_OK
        )