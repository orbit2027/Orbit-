"""
Vistas API para el módulo de proyectos.
Implementa CRUD y la consulta global del admin.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.usuarios.modelo import Usuario
from apps.tareas.modelo import Tarea
from apps.middlewares.roles import requerir_rol
from .modelo import Proyecto
from .serializador import ProyectoSerializador

def _serializar_con_metricas(proyecto):
    """Serializa un proyecto y le añade conteo de tareas asociadas."""
    datos = ProyectoSerializador(proyecto).data
    tareas = Tarea.objects(proyecto=str(proyecto.id))
    datos['tareas_totales'] = tareas.count()
    datos['tareas_completadas'] = tareas(estado='completado').count()
    datos['tareas_activas'] = tareas(
        estado__in=['por_hacer', 'en_progreso']
    ).count()
    return datos

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def lista_proyectos(request):
    """Crear o visualizar los proyectos propios."""
    if request.method == 'GET':
        proyectos = Proyecto.objects(usuario=request.user).order_by('-fecha_creacion')
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
        proyecto = Proyecto.objects.get(id=proyecto_id, usuario=request.user)
    except Proyecto.DoesNotExist:
        return Response(
            {'error': 'Proyecto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
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
            for t in Tarea.objects(proyecto=str(proyecto.id)).order_by('-fecha_creacion')
        ]
        return Response(datos, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
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
        # Las tareas del proyecto se conservan, solo se desvinculan
        Tarea.objects(proyecto=str(proyecto.id)).update(set__proyecto='')
        proyecto.delete()
        return Response(
            {'mensaje': 'Proyecto eliminado'},
            status=status.HTTP_200_OK
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def archivar_proyecto(request, proyecto_id):
    """Archivar/restaurar un proyecto cambiando su estado."""
    try:
        proyecto = Proyecto.objects.get(id=proyecto_id, usuario=request.user)
    except Proyecto.DoesNotExist:
        return Response(
            {'error': 'Proyecto no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    proyecto.estado = 'archivado' if proyecto.estado == 'activo' else 'activo'
    proyecto.save()

    return Response({
        'mensaje': f"Proyecto {'archivado' if proyecto.estado == 'archivado' else 'restaurado'}",
        'estado': proyecto.estado
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def proyectos_todos(request):
    """
    Visualizar los proyectos de todos los usuarios (solo admin).
    Incluye el nombre del propietario en cada proyecto.
    """
    proyectos = Proyecto.objects().order_by('-fecha_creacion')
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