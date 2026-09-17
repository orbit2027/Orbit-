"""
Vistas API para el módulo de compartición.
Permiten compartir tareas y proyectos con otros usuarios por correo.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.usuarios.modelo import Usuario
from apps.tareas.modelo import Tarea
from apps.proyectos.modelo import Proyecto

from .modelo import Comparticion
from .serializador import (
    ComparticionSerializador,
    PermisoSerializador,
    ComparticionSalidaSerializador,
)
from .permisos import (
    nivel_sobre_tarea,
    nivel_sobre_proyecto,
    puede_administrar,
)


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_comparticion(request):
    """Comparte un objeto con otro usuario por correo (dueño o administrar)."""
    serializador = ComparticionSerializador(data=request.data)
    if not serializador.is_valid():
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    datos = serializador.validated_data
    correo = datos['correo'].lower().strip()
    tipo_objeto = datos['tipo_objeto']
    objeto_id = datos['objeto_id']
    permiso = datos['permiso']

    invitado = Usuario.objects.filter(correo=correo).first()
    if not invitado:
        return Response(
            {'error': 'No existe ninguna cuenta con ese correo.'},
            status=status.HTTP_404_NOT_FOUND
        )
    if invitado.id == request.user.id:
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

    comparticion, _creada = Comparticion.objects.update_or_create(
        compartido_con=invitado,
        tipo_objeto=tipo_objeto,
        objeto_id=objeto_id,
        defaults={
            'propietario': request.user,
            'permiso': permiso,
        }
    )

    return Response(
        ComparticionSalidaSerializador(comparticion).data,
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_comparticiones(request, tipo_objeto, objeto_id):
    """Lista las comparticiones de un objeto (solo dueño/administrar)."""
    if not _puede_administrar_objeto(request.user, tipo_objeto, objeto_id):
        return Response(
            {'error': 'No tienes permisos para ver las comparticiones.'},
            status=status.HTTP_403_FORBIDDEN
        )

    compartidas = Comparticion.objects.filter(
        tipo_objeto=tipo_objeto, objeto_id=objeto_id
    ).order_by('-fecha_compartida')
    return Response(
        [ComparticionSalidaSerializador(c).data for c in compartidas],
        status=status.HTTP_200_OK
    )


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def detalle_comparticion(request, comparticion_id):
    """Cambia el permiso o elimina una compartición."""
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
        comparticion.save()
        return Response(
            ComparticionSalidaSerializador(comparticion).data,
            status=status.HTTP_200_OK
        )

    comparticion.delete()
    return Response(
        {'mensaje': 'Compartición eliminada'},
        status=status.HTTP_200_OK
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