"""
Vistas API para el modulo de administracion.
Gestion de usuarios y estadisticas globales del sistema.
"""
from datetime import datetime, timedelta
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer

from apps.usuarios.modelo import Usuario
from apps.tareas.modelo import Tarea
from apps.middlewares.roles import requerir_rol
from .serializador import (
    UsuarioAdminSerializador,
    CrearUsuarioAdminSerializador,
    EditarUsuarioAdminSerializador,
    EstadisticasGlobalesSerializador,
    ToggleUsuarioRespuestaSerializador,
)

MensajeSerializador = inline_serializer(
    name='AdminMensaje', fields={'mensaje': serializers.CharField()}
)

@extend_schema(
    tags=['Administración'],
    summary='Estadísticas globales (admin)',
    responses={200: EstadisticasGlobalesSerializador, 403: None},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def estadisticas_globales(request):
    ahora = datetime.utcnow()
    inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

    total_usuarios = Usuario.objects.count()
    tareas_activas = Tarea.objects.filter(estado__in=['por_hacer', 'en_progreso']).count()
    completadas_hoy = Tarea.objects.filter(
        estado='completado',
        fecha_creacion__gte=inicio_dia
    ).count()
    activos_hoy = Usuario.objects.filter(
        activo=True,
        fecha_registro__gte=inicio_dia
    ).count()

    # Crecimiento mensual de los ultimos 6 meses
    crecimiento = []
    for i in range(5, -1, -1):
        fecha_inicio = ahora - timedelta(days=30 * (i + 1))
        fecha_fin = ahora - timedelta(days=30 * i)

        registros = Usuario.objects.filter(
            fecha_registro__gte=fecha_inicio,
            fecha_registro__lt=fecha_fin
        ).count()

        crecimiento.append({
            'mes': fecha_inicio.strftime('%b'),
            'registros': registros
        })

    return Response({
        'total_usuarios': total_usuarios,
        'tareas_activas': tareas_activas,
        'completadas_hoy': completadas_hoy,
        'activos_hoy': activos_hoy,
        'crecimiento_mensual': crecimiento
    })


@extend_schema(
    tags=['Administración'],
    summary='Listar usuarios (admin)',
    description='RF-GES-02. Todos los usuarios registrados.',
    responses={200: UsuarioAdminSerializador(many=True), 403: None},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def listar_usuarios(request):
    """RF-GES-02: Visualizar todos los usuarios registrados."""
    usuarios = Usuario.objects.order_by('-fecha_registro')
    serializador = UsuarioAdminSerializador(usuarios, many=True)
    return Response(serializador.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Administración'],
    summary='Crear usuario (admin)',
    request=CrearUsuarioAdminSerializador,
    responses={201: UsuarioAdminSerializador, 400: None, 403: None},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def crear_usuario(request):
    serializador = CrearUsuarioAdminSerializador(data=request.data)
    if serializador.is_valid():
        usuario = serializador.save()
        return Response(
            UsuarioAdminSerializador(usuario).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Administración'],
    summary='Ver detalle de usuario (admin)',
    responses={200: UsuarioAdminSerializador, 403: None, 404: None},
)
@extend_schema(
    tags=['Administración'],
    summary='Editar usuario (admin)',
    request=EditarUsuarioAdminSerializador,
    responses={200: UsuarioAdminSerializador, 400: None, 403: None, 404: None},
)
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def detalle_usuario(request, usuario_id):
  
    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializador = UsuarioAdminSerializador(usuario)
        return Response(serializador.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializador = EditarUsuarioAdminSerializador(
            data=request.data,
            context={'usuario_id': usuario_id}
        )
        if serializador.is_valid():
            datos = serializador.validated_data
            if 'nombre_completo' in datos:
                usuario.nombre_completo = datos['nombre_completo']
            if 'correo' in datos:
                usuario.correo = datos['correo']
            if 'rol' in datos:
                usuario.rol = datos['rol']
            usuario.save()
            return Response(
                UsuarioAdminSerializador(usuario).data,
                status=status.HTTP_200_OK
            )
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Administración'],
    summary='Activar o desactivar usuario (admin)',
    request=None,
    responses={200: ToggleUsuarioRespuestaSerializador, 403: None, 404: None},
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def toggle_usuario(request, usuario_id):
    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    usuario.activo = not usuario.activo
    usuario.save()

    return Response({
        'mensaje': f"Usuario {'activado' if usuario.activo else 'desactivado'}",
        'activo': usuario.activo
    }, status=status.HTTP_200_OK)