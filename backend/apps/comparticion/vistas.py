"""
Vistas API para el módulo de compartición.

Flujo de invitación:
1. El dueño (o alguien con permiso administrar) invita por correo.
2. Se crea una `Invitacion` pendiente y se envía un correo con un enlace.
3. La persona invitada acepta o rechaza desde la app o desde el enlace.
4. Solo al aceptar se crea la `Comparticion` que otorga acceso.
"""
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer

from apps.usuarios.modelo import Usuario
from apps.tareas.modelo import Tarea
from apps.proyectos.modelo import Proyecto
from apps.email.correos import (
    correo_invitacion_compartir,
    correo_invitacion_aceptada,
)

from .modelo import Comparticion, Invitacion
from .serializador import (
    ComparticionSerializador,
    PermisoSerializador,
    RespuestaInvitacionSerializador,
    ComparticionSalidaSerializador,
    ComparticionConmigoSalidaSerializador,
    InvitacionSalidaSerializador,
    InvitacionRecibidaSalidaSerializador,
)
from .permisos import (
    nivel_sobre_tarea,
    nivel_sobre_proyecto,
    puede_administrar,
)

MensajeSerializador = inline_serializer(
    name='ComparticionMensaje', fields={'mensaje': serializers.CharField()}
)

PERMISOS_TEXTO = {
    'ver': 'Puede ver',
    'editar': 'Puede ver y editar',
    'administrar': 'Puede administrar y compartir',
}


def _normalizar_correo(correo):
    return (correo or '').strip().lower()


def _puede_administrar_objeto(usuario, tipo_objeto, objeto_id):
    """El requester es dueño o tiene permiso administrar sobre el objeto."""
    if tipo_objeto == 'proyecto':
        proyecto = Proyecto.objects.filter(id=objeto_id).first()
        if not proyecto:
            return False
        return puede_administrar(nivel_sobre_proyecto(usuario, proyecto))

    tarea = Tarea.objects.filter(id=objeto_id).first()
    if not tarea:
        return False
    return puede_administrar(nivel_sobre_tarea(usuario, tarea))


def _objeto_existe(tipo_objeto, objeto_id):
    """Valida que el objeto compartido exista."""
    if tipo_objeto == 'proyecto':
        return Proyecto.objects.filter(id=objeto_id).exists()
    return Tarea.objects.filter(id=objeto_id).exists()


def _titulo_objeto(tipo_objeto, objeto_id):
    """Título legible del objeto para listados."""
    if tipo_objeto == 'proyecto':
        proyecto = Proyecto.objects.filter(id=objeto_id).first()
        return proyecto.nombre if proyecto else 'Proyecto eliminado'
    tarea = Tarea.objects.filter(id=objeto_id).first()
    return tarea.titulo if tarea else 'Tarea eliminada'


def _enviar_invitacion(invitacion):
    """Envía el correo con el enlace para aceptar la invitación."""
    correo_invitacion_compartir(
        invitacion.correo,
        invitacion.propietario,
        invitacion,
        _titulo_objeto(invitacion.tipo_objeto, invitacion.objeto_id),
    )


@extend_schema(
    tags=['Compartición'],
    summary='Invitar a compartir una tarea o proyecto',
    description=(
        'Envía una invitación por correo. La persona invitada obtiene acceso '
        'solo después de aceptarla (requiere ser dueño o administrar).'
    ),
    request=ComparticionSerializador,
    responses={200: ComparticionSalidaSerializador, 400: None, 403: None, 404: None},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_comparticion(request):
    """Invita por correo a una tarea o proyecto (dueño o administrar)."""
    serializador = ComparticionSerializador(data=request.data)
    if not serializador.is_valid():
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    datos = serializador.validated_data
    correo = _normalizar_correo(datos['correo'])
    tipo_objeto = datos['tipo_objeto']
    objeto_id = datos['objeto_id']
    permiso = datos['permiso']

    if correo == _normalizar_correo(request.user.correo):
        return Response(
            {'error': 'No puedes compartir un elemento contigo mismo.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not _objeto_existe(tipo_objeto, objeto_id):
        return Response(
            {'error': 'El elemento que intentas compartir no existe.'},
            status=status.HTTP_404_NOT_FOUND
        )
    if not _puede_administrar_objeto(request.user, tipo_objeto, objeto_id):
        return Response(
            {'error': 'No tienes permisos para compartir este elemento.'},
            status=status.HTTP_403_FORBIDDEN
        )

    invitado = Usuario.objects.filter(correo__iexact=correo).first()

    # Si la persona ya tiene acceso aceptado, solo se actualiza el permiso.
    if invitado:
        comparticion = Comparticion.objects.filter(
            compartido_con=invitado,
            tipo_objeto=tipo_objeto,
            objeto_id=objeto_id,
        ).first()
        if comparticion:
            comparticion.permiso = permiso
            comparticion.propietario = request.user
            comparticion.save(update_fields=['permiso', 'propietario'])
            salida = ComparticionSalidaSerializador(comparticion).data
            salida['correo_enviado'] = False
            salida['ya_tiene_acceso'] = True
            return Response(salida, status=status.HTTP_200_OK)

    invitacion, creada = Invitacion.objects.get_or_create(
        correo=correo,
        tipo_objeto=tipo_objeto,
        objeto_id=objeto_id,
        defaults={
            'propietario': request.user,
            'permiso': permiso,
        }
    )

    if not creada:
        # Ya existe una invitación: si sigue pendiente solo se actualiza el
        # permiso (sin reenviar correo). Si fue rechazada o su acceso ya no
        # existe, se reactiva y se envía el correo otra vez.
        reactivada = invitacion.estado != 'pendiente'
        invitacion.propietario = request.user
        invitacion.permiso = permiso
        invitacion.estado = 'pendiente'
        invitacion.fecha_respuesta = None
        if reactivada:
            invitacion.fecha_creacion = timezone.now()
        invitacion.save()
        if not reactivada:
            salida = InvitacionSalidaSerializador(invitacion).data
            salida['correo_enviado'] = False
            return Response(salida, status=status.HTTP_200_OK)

    _enviar_invitacion(invitacion)
    salida = InvitacionSalidaSerializador(invitacion).data
    salida['correo_enviado'] = True
    salida['creada'] = creada
    return Response(salida, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Compartición'],
    summary='Listar accesos e invitaciones de un objeto',
    description='Quién tiene acceso y quién tiene invitaciones pendientes (dueño o administrar).',
    responses={200: InvitacionSalidaSerializador(many=True), 403: None},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_comparticiones(request, tipo_objeto, objeto_id):
    """Lista accesos aceptados e invitaciones de un objeto."""
    if not _puede_administrar_objeto(request.user, tipo_objeto, objeto_id):
        return Response(
            {'error': 'No tienes permisos para ver las comparticiones.'},
            status=status.HTTP_403_FORBIDDEN
        )

    compartidas = Comparticion.objects.filter(
        tipo_objeto=tipo_objeto, objeto_id=objeto_id
    ).order_by('-fecha_compartida')
    invitaciones = Invitacion.objects.filter(
        tipo_objeto=tipo_objeto, objeto_id=objeto_id
    ).order_by('-fecha_creacion')

    # Las invitaciones aceptadas ya aparecen como compartición: se omiten.
    resultado = [ComparticionSalidaSerializador(c).data for c in compartidas]
    resultado += [
        InvitacionSalidaSerializador(i).data
        for i in invitaciones if i.estado != 'aceptada'
    ]
    resultado.sort(key=lambda d: d.get('fecha_compartida') or '', reverse=True)
    return Response(resultado, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Compartición'],
    summary='Cambiar permiso de una compartición',
    request=PermisoSerializador,
    responses={200: ComparticionSalidaSerializador, 400: None, 403: None, 404: None},
)
@extend_schema(
    tags=['Compartición'],
    summary='Eliminar una compartición',
    responses={200: MensajeSerializador, 403: None, 404: None},
)
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def detalle_comparticion(request, comparticion_id):
    """Cambia el permiso o elimina una compartición aceptada."""
    comparticion = Comparticion.objects.filter(id=comparticion_id).first()
    if not comparticion:
        return Response(
            {'error': 'Compartición no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not _puede_administrar_objeto(
        request.user, comparticion.tipo_objeto, comparticion.objeto_id
    ):
        return Response(
            {'error': 'No tienes permisos sobre esta compartición.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'PATCH':
        serializador = PermisoSerializador(data=request.data)
        if not serializador.is_valid():
            return Response(
                serializador.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        comparticion.permiso = serializador.validated_data['permiso']
        comparticion.save(update_fields=['permiso'])
        return Response(
            ComparticionSalidaSerializador(comparticion).data,
            status=status.HTTP_200_OK
        )

    comparticion.delete()
    return Response(
        {'mensaje': 'Compartición eliminada'},
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Compartición'],
    summary='Editar o cancelar una invitación',
    request=PermisoSerializador,
    responses={200: InvitacionSalidaSerializador, 403: None, 404: None},
)
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def detalle_invitacion(request, invitacion_id):
    """Cambia el permiso de una invitación pendiente o la cancela."""
    invitacion = Invitacion.objects.filter(id=invitacion_id).first()
    if not invitacion:
        return Response(
            {'error': 'Invitación no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    if not _puede_administrar_objeto(
        request.user, invitacion.tipo_objeto, invitacion.objeto_id
    ):
        return Response(
            {'error': 'No tienes permisos sobre esta invitación.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'PATCH':
        serializador = PermisoSerializador(data=request.data)
        if not serializador.is_valid():
            return Response(
                serializador.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        invitacion.permiso = serializador.validated_data['permiso']
        invitacion.save(update_fields=['permiso'])
        return Response(
            InvitacionSalidaSerializador(invitacion).data,
            status=status.HTTP_200_OK
        )

    invitacion.delete()
    return Response(
        {'mensaje': 'Invitación cancelada'},
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Compartición'],
    summary='Reenviar una invitación',
    description='Reenvía el correo de invitación y, si fue rechazada, la reactiva.',
    responses={200: InvitacionSalidaSerializador, 403: None, 404: None},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reenviar_invitacion(request, invitacion_id):
    """Reenvía el correo de una invitación pendiente o rechazada."""
    invitacion = Invitacion.objects.filter(id=invitacion_id).first()
    if not invitacion:
        return Response(
            {'error': 'Invitación no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    if not _puede_administrar_objeto(
        request.user, invitacion.tipo_objeto, invitacion.objeto_id
    ):
        return Response(
            {'error': 'No tienes permisos sobre esta invitación.'},
            status=status.HTTP_403_FORBIDDEN
        )
    if not _objeto_existe(invitacion.tipo_objeto, invitacion.objeto_id):
        return Response(
            {'error': 'El elemento ya no existe.'},
            status=status.HTTP_404_NOT_FOUND
        )

    invitacion.estado = 'pendiente'
    invitacion.fecha_respuesta = None
    invitacion.save(update_fields=['estado', 'fecha_respuesta'])
    _enviar_invitacion(invitacion)
    return Response(
        InvitacionSalidaSerializador(invitacion).data,
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Compartición'],
    summary='Invitaciones pendientes para mí',
    description='Lista las invitaciones enviadas a mi correo que aún no respondo.',
    responses={200: InvitacionRecibidaSalidaSerializador(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_invitaciones(request):
    """Invitaciones pendientes dirigidas al correo del usuario autenticado."""
    invitaciones = Invitacion.objects.filter(
        correo__iexact=request.user.correo,
        estado='pendiente',
    ).select_related('propietario').order_by('-fecha_creacion')

    return Response(
        [
            InvitacionRecibidaSalidaSerializador(i).data
            for i in invitaciones
            if _objeto_existe(i.tipo_objeto, i.objeto_id)
        ],
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Compartición'],
    summary='Aceptar o rechazar una invitación',
    request=RespuestaInvitacionSerializador,
    responses={200: MensajeSerializador, 400: None, 403: None, 404: None},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def responder_invitacion(request, referencia):
    """
    Acepta o rechaza una invitación.

    `referencia` puede ser el id numérico o el token enviado por correo.
    """
    serializador = RespuestaInvitacionSerializador(data=request.data)
    if not serializador.is_valid():
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    consulta = {'id': referencia} if str(referencia).isdigit() else {'token': referencia}
    invitacion = Invitacion.objects.filter(**consulta).first()
    if not invitacion:
        return Response(
            {'error': 'La invitación no existe o el enlace no es válido.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if _normalizar_correo(invitacion.correo) != _normalizar_correo(request.user.correo):
        return Response(
            {
                'error': (
                    'Esta invitación es para '
                    f'{invitacion.correo}. Inicia sesión con esa cuenta.'
                )
            },
            status=status.HTTP_403_FORBIDDEN
        )

    if invitacion.estado != 'pendiente':
        if invitacion.estado == 'aceptada':
            return Response(
                {'mensaje': 'Ya habías aceptado esta invitación.'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Esta invitación ya fue respondida.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not serializador.validated_data['aceptar']:
        invitacion.estado = 'rechazada'
        invitacion.fecha_respuesta = timezone.now()
        invitacion.save(update_fields=['estado', 'fecha_respuesta'])
        return Response(
            {'mensaje': 'Invitación rechazada'},
            status=status.HTTP_200_OK
        )

    if not _objeto_existe(invitacion.tipo_objeto, invitacion.objeto_id):
        invitacion.estado = 'rechazada'
        invitacion.fecha_respuesta = timezone.now()
        invitacion.save(update_fields=['estado', 'fecha_respuesta'])
        return Response(
            {'error': 'El elemento compartido ya no existe.'},
            status=status.HTTP_404_NOT_FOUND
        )

    Comparticion.objects.update_or_create(
        compartido_con=request.user,
        tipo_objeto=invitacion.tipo_objeto,
        objeto_id=invitacion.objeto_id,
        defaults={
            'propietario': invitacion.propietario,
            'permiso': invitacion.permiso,
        }
    )

    invitacion.estado = 'aceptada'
    invitacion.fecha_respuesta = timezone.now()
    invitacion.save(update_fields=['estado', 'fecha_respuesta'])

    titulo = _titulo_objeto(invitacion.tipo_objeto, invitacion.objeto_id)
    correo_invitacion_aceptada(
        invitacion.propietario, request.user, invitacion.tipo_objeto, titulo
    )

    return Response(
        {
            'mensaje': 'Invitación aceptada',
            'titulo': titulo,
            'tipo_objeto': invitacion.tipo_objeto,
            'permiso': invitacion.permiso,
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Compartición'],
    summary='Objetos compartidos conmigo',
    description='Lista tareas y proyectos que otros usuarios compartieron con el autenticado.',
    responses={200: ComparticionConmigoSalidaSerializador(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def compartidos_conmigo(request):
    """Lista los objetos que otros usuarios compartieron con el actual."""
    compartidas = Comparticion.objects.filter(
        compartido_con=request.user
    ).order_by('-fecha_compartida')

    resultado = []
    for c in compartidas:
        datos = ComparticionSalidaSerializador(c).data
        datos['titulo'] = _titulo_objeto(c.tipo_objeto, c.objeto_id)
        datos['propietario'] = c.propietario.nombre_completo
        resultado.append(datos)
    return Response(resultado, status=status.HTTP_200_OK)
