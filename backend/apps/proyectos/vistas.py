"""
Vistas API para el módulo de proyectos.
Implementa CRUD y la consulta global del admin.
"""
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from drf_spectacular.utils import extend_schema, inline_serializer

from apps.usuarios.modelo import Usuario
from apps.tareas.modelo import Tarea
from apps.comparticion.modelo import Comparticion
from apps.comparticion.permisos import (
    nivel_sobre_proyecto,
    puede_ver,
    puede_editar,
    puede_administrar,
)
from apps.middlewares.roles import requerir_rol
from .modelo import Proyecto
from .serializador import (
    ProyectoSerializador,
    ProyectoConMetricasSerializador,
    ProyectoDetalleSerializador,
    ProyectoConPropietarioSerializador,
)

MensajeEstadoSerializador = inline_serializer(
    name='ProyectoMensajeEstado',
    fields={'mensaje': serializers.CharField(), 'estado': serializers.CharField()},
)
MensajeSerializador = inline_serializer(
    name='ProyectoMensaje', fields={'mensaje': serializers.CharField()}
)

def _serializar_con_metricas(proyecto):
    """Serializa un proyecto y le añade conteo de tareas asociadas."""
    datos = ProyectoSerializador(proyecto).data
    tareas = Tarea.objects.filter(proyecto=str(proyecto.id))
    datos['tareas_totales'] = tareas.count()
    datos['tareas_completadas'] = tareas.filter(estado='completado').count()
    datos['tareas_activas'] = tareas.filter(
        estado__in=['por_hacer', 'en_progreso']
    ).count()
    return datos

@extend_schema(
    tags=['Proyectos'],
    summary='Listar proyectos',
    description='Proyectos propios y compartidos con el usuario.',
    responses={200: ProyectoConMetricasSerializador(many=True)},
)
@extend_schema(
    tags=['Proyectos'],
    summary='Crear proyecto',
    request=ProyectoSerializador,
    responses={201: ProyectoSerializador, 400: None},
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def lista_proyectos(request):
    """Crear o visualizar los proyectos propios."""
    if request.method == 'GET':
        # Propios + compartidos con el usuario
        proyectos_compartidos = Comparticion.objects.filter(
            compartido_con=request.user, tipo_objeto='proyecto'
        ).values_list('objeto_id', flat=True)
        proyectos = Proyecto.objects.filter(
            Q(usuario=request.user) | Q(id__in=list(proyectos_compartidos))
        ).order_by('-fecha_creacion')
        return Response(
            [_serializar_con_metricas(p) for p in proyectos],
            status=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        serializador = ProyectoSerializador(data=request.data)
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
    tags=['Proyectos'],
    summary='Ver detalle de proyecto',
    description='Incluye métricas y la lista de tareas del proyecto.',
    responses={200: ProyectoDetalleSerializador, 403: None, 404: None},
)
@extend_schema(
    tags=['Proyectos'],
    summary='Editar proyecto',
    request=ProyectoSerializador,
    responses={200: ProyectoConMetricasSerializador, 400: None, 403: None, 404: None},
)
@extend_schema(
    tags=['Proyectos'],
    summary='Eliminar proyecto',
    description='Las tareas asociadas se conservan y quedan sin proyecto.',
    responses={200: MensajeSerializador, 403: None, 404: None},
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def detalle_proyecto(request, proyecto_id):
    """
    Ver detalle, editar o eliminar un proyecto.

    GET: incluye la lista de tareas del proyecto.
    PUT/PATCH: edita nombre, descripción, color, estado y fecha límite.
    DELETE: elimina el proyecto. Las tareas asociadas quedan sin proyecto.
    """
    try:
        proyecto = Proyecto.objects.get(id=proyecto_id)
    except Proyecto.DoesNotExist:
        return Response(
            {'error': 'Proyecto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    nivel = nivel_sobre_proyecto(request.user, proyecto)

    if request.method == 'GET':
        if not puede_ver(nivel):
            return Response(
                {'error': 'No tienes acceso a este proyecto.'},
                status=status.HTTP_403_FORBIDDEN
            )
        datos = _serializar_con_metricas(proyecto)
        datos['tareas'] = [
            {
                'id': str(t.id),
                'titulo': t.titulo,
                'estado': t.estado,
                'etiqueta': t.etiqueta or '',
                'color_etiqueta': t.color_etiqueta,
                'fecha_limite': (
                    t.fecha_limite.isoformat() if t.fecha_limite else None
                ),
            }
            for t in Tarea.objects.filter(proyecto=str(proyecto.id)).order_by('-fecha_creacion')
        ]
        return Response(datos, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        if not puede_editar(nivel):
            return Response(
                {'error': 'No tienes permisos para editar este proyecto.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializador = ProyectoSerializador(
            proyecto,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        if serializador.is_valid():
            serializador.save()
            return Response(
                _serializar_con_metricas(proyecto),
                status=status.HTTP_200_OK
            )
        return Response(
            serializador.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        if not puede_administrar(nivel):
            return Response(
                {'error': 'No tienes permisos para eliminar este proyecto.'},
                status=status.HTTP_403_FORBIDDEN
            )
        # Las tareas del proyecto se conservan, solo se desvinculan
        Tarea.objects.filter(proyecto=str(proyecto.id)).update(proyecto='')
        proyecto.delete()
        return Response(
            {'mensaje': 'Proyecto eliminado'},
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=['Proyectos'],
    summary='Archivar o restaurar proyecto',
    description='Alterna el estado del proyecto entre activo y archivado.',
    request=None,
    responses={200: MensajeEstadoSerializador, 403: None, 404: None},
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def archivar_proyecto(request, proyecto_id):
    """Archivar/restaurar un proyecto cambiando su estado."""
    try:
        proyecto = Proyecto.objects.get(id=proyecto_id)
    except Proyecto.DoesNotExist:
        return Response(
            {'error': 'Proyecto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not puede_editar(nivel_sobre_proyecto(request.user, proyecto)):
        return Response(
            {'error': 'No tienes permisos para archivar este proyecto.'},
            status=status.HTTP_403_FORBIDDEN
        )

    proyecto.estado = 'archivado' if proyecto.estado == 'activo' else 'activo'
    proyecto.save()

    return Response({
        'mensaje': f"Proyecto {'archivado' if proyecto.estado == 'archivado' else 'restaurado'}",
        'estado': proyecto.estado
    }, status=status.HTTP_200_OK)

@extend_schema(
    tags=['Administración'],
    summary='Listar todos los proyectos (admin)',
    description='Incluye el nombre del propietario en cada proyecto.',
    responses={200: ProyectoConPropietarioSerializador(many=True), 403: None},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def proyectos_todos(request):
    """
    Visualizar los proyectos de todos los usuarios (solo admin).
    Incluye el nombre del propietario en cada proyecto.
    """
    proyectos = Proyecto.objects.order_by('-fecha_creacion')
    resultado = []
    for p in proyectos:
        datos = _serializar_con_metricas(p)
        try:
            propietario = Usuario.objects.get(id=p.usuario.id)
            datos['propietario'] = propietario.nombre_completo
        except Usuario.DoesNotExist:
            datos['propietario'] = 'Usuario eliminado'
        resultado.append(datos)
    return Response(resultado, status=status.HTTP_200_OK)