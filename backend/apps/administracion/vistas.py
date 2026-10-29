"""
Vistas API para el modulo de administracion.
Gestion de usuarios y estadisticas globales del sistema.
"""
from datetime import datetime, timedelta
from django.db.models import Count, Q
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer

from apps.usuarios.modelo import (
    MENSAJE_ULTIMO_ADMIN,
    Usuario,
    es_ultimo_administrador,
)
from apps.tareas.modelo import Tarea
from apps.tareas.serializador import TareaSerializador
from apps.proyectos.modelo import Proyecto
from apps.proyectos.serializador import ProyectoSerializador
from apps.middlewares.roles import requerir_rol
from apps.email.correos import correo_bienvenida
from .models import obtener_configuracion
from .politica_contrasena import obtener_politica_contrasena
from .serializador import (
    UsuarioAdminSerializador,
    CrearUsuarioAdminSerializador,
    EditarUsuarioAdminSerializador,
    EstadisticasGlobalesSerializador,
    ToggleUsuarioRespuestaSerializador,
    ConfiguracionAdminSerializador,
    ConfiguracionPublicaSerializador,
    TareaModeracionAdminSerializador,
    ProyectoModeracionAdminSerializador,
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
    usuarios_activos = Usuario.objects.filter(activo=True).count()
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
        'usuarios_activos': usuarios_activos,
        'tareas_activas': tareas_activas,
        'completadas_hoy': completadas_hoy,
        'activos_hoy': activos_hoy,
        'proyectos_totales': Proyecto.objects.count(),
        'proyectos_activos': Proyecto.objects.filter(estado='activo').count(),
        'proyectos_archivados': Proyecto.objects.filter(estado='archivado').count(),
        'crecimiento_mensual': crecimiento
    })


@extend_schema(
    tags=['Administración'],
    summary='Consultar configuración pública',
    responses={200: ConfiguracionPublicaSerializador},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def configuracion_publica(request):
    configuracion = obtener_configuracion()
    return Response({
        'aviso_global': configuracion.aviso_global,
        'mantenimiento_activo': configuracion.mantenimiento_activo,
        'mensaje_mantenimiento': configuracion.mensaje_mantenimiento,
        'politica_contrasena': obtener_politica_contrasena(),
    })


@extend_schema(
    tags=['Administración'],
    summary='Consultar o actualizar configuración (admin)',
    request=ConfiguracionAdminSerializador,
    responses={200: ConfiguracionAdminSerializador, 400: None, 403: None},
)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def configuracion_admin(request):
    configuracion = obtener_configuracion()
    if request.method == 'GET':
        return Response(ConfiguracionAdminSerializador(configuracion).data)

    serializador = ConfiguracionAdminSerializador(
        data=request.data,
        partial=request.method == 'PATCH',
    )
    if not serializador.is_valid():
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    for campo, valor in serializador.validated_data.items():
        setattr(configuracion, campo, valor)
    configuracion.save()
    return Response(ConfiguracionAdminSerializador(configuracion).data)


@extend_schema(
    tags=['Administración'],
    summary='Listar todas las tareas para moderación (admin)',
    responses={200: TareaModeracionAdminSerializador(many=True), 403: None},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def tareas_todas(request):
    tareas = Tarea.objects.select_related('usuario').order_by('-fecha_creacion')
    return Response([
        {
            'id': str(tarea.id),
            'titulo': tarea.titulo,
            'descripcion': tarea.descripcion or '',
            'estado': tarea.estado,
            'etiqueta': tarea.etiqueta or '',
            'fecha_limite': tarea.fecha_limite,
            'propietario': tarea.usuario.nombre_completo,
            'correo_propietario': tarea.usuario.correo,
        }
        for tarea in tareas
    ])


@extend_schema(
    tags=['Administración'],
    summary='Editar o eliminar tarea (admin)',
    request=TareaSerializador,
    responses={200: TareaModeracionAdminSerializador, 400: None, 403: None, 404: None},
)
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def moderar_tarea(request, tarea_id):
    try:
        tarea = Tarea.objects.select_related('usuario').get(id=tarea_id)
    except Tarea.DoesNotExist:
        return Response(
            {'error': 'Tarea no encontrada'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'DELETE':
        tarea.delete()
        return Response({'mensaje': 'Tarea eliminada'})

    serializador = TareaSerializador(tarea, data=request.data, partial=True)
    if not serializador.is_valid():
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)
    tarea = serializador.save()
    return Response({
        'id': str(tarea.id),
        'titulo': tarea.titulo,
        'descripcion': tarea.descripcion or '',
        'estado': tarea.estado,
        'etiqueta': tarea.etiqueta or '',
        'fecha_limite': tarea.fecha_limite,
        'propietario': tarea.usuario.nombre_completo,
        'correo_propietario': tarea.usuario.correo,
    })


@extend_schema(
    tags=['Administración'],
    summary='Listar todos los proyectos para moderación (admin)',
    responses={200: ProyectoModeracionAdminSerializador(many=True), 403: None},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def proyectos_todos(request):
    proyectos = Proyecto.objects.select_related('usuario').order_by('-fecha_creacion')
    conteos_tareas = {
        fila['proyecto']: fila
        for fila in Tarea.objects.values('proyecto').annotate(
            tareas_totales=Count('id'),
            tareas_completadas=Count(
                'id', filter=Q(estado='completado')
            ),
        )
    }
    return Response([
        {
            'id': str(proyecto.id),
            'nombre': proyecto.nombre,
            'descripcion': proyecto.descripcion or '',
            'estado': proyecto.estado,
            'fecha_limite': proyecto.fecha_limite,
            'propietario': proyecto.usuario.nombre_completo,
            'correo_propietario': proyecto.usuario.correo,
            'tareas_totales': conteos_tareas.get(
                str(proyecto.id), {}
            ).get('tareas_totales', 0),
            'tareas_completadas': conteos_tareas.get(
                str(proyecto.id), {}
            ).get('tareas_completadas', 0),
        }
        for proyecto in proyectos
    ])


@extend_schema(
    tags=['Administración'],
    summary='Editar o eliminar proyecto (admin)',
    request=ProyectoSerializador,
    responses={200: ProyectoModeracionAdminSerializador, 400: None, 403: None, 404: None},
)
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@requerir_rol('administrador')
def moderar_proyecto(request, proyecto_id):
    try:
        proyecto = Proyecto.objects.select_related('usuario').get(id=proyecto_id)
    except Proyecto.DoesNotExist:
        return Response(
            {'error': 'Proyecto no encontrado'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'DELETE':
        Tarea.objects.filter(proyecto=str(proyecto.id)).update(proyecto='')
        proyecto.delete()
        return Response({
            'mensaje': 'Proyecto eliminado; sus tareas quedaron sin proyecto.'
        })

    serializador = ProyectoSerializador(
        proyecto, data=request.data, partial=True
    )
    if not serializador.is_valid():
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)
    proyecto = serializador.save()
    return Response({
        'id': str(proyecto.id),
        'nombre': proyecto.nombre,
        'descripcion': proyecto.descripcion or '',
        'estado': proyecto.estado,
        'fecha_limite': proyecto.fecha_limite,
        'propietario': proyecto.usuario.nombre_completo,
        'correo_propietario': proyecto.usuario.correo,
        'tareas_totales': Tarea.objects.filter(
            proyecto=str(proyecto.id)
        ).count(),
        'tareas_completadas': Tarea.objects.filter(
            proyecto=str(proyecto.id), estado='completado'
        ).count(),
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
        correo_bienvenida(usuario)
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
    description='No permite desactivar al último administrador activo: dejaría '
                'la aplicación sin administración.',
    request=None,
    responses={200: ToggleUsuarioRespuestaSerializador, 400: None, 403: None, 404: None},
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

    # Desactivar al último administrador dejaría la app sin acceso a la
    # administración: nadie podría volver a activarlo (el login exige activo).
    if usuario.activo and es_ultimo_administrador(usuario):
        return Response(
            {'error': MENSAJE_ULTIMO_ADMIN},
            status=status.HTTP_400_BAD_REQUEST
        )

    usuario.activo = not usuario.activo
    if not usuario.activo:
        # Invalida los JWT emitidos: si la cuenta se reactiva, las sesiones
        # viejas no vuelven a servir.
        usuario.session_version += 1
    usuario.save()

    return Response({
        'mensaje': f"Usuario {'activado' if usuario.activo else 'desactivado'}",
        'activo': usuario.activo
    }, status=status.HTTP_200_OK)