
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .modelo import Tarea
from .serializador import TareaSerializador, MoverTareaSerializador

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def lista_tareas(request):
    if request.method == 'GET':
        tareas = Tarea.objects.filter(usuario=request.user).order_by('-fecha_creacion')
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


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def detalle_tarea(request, tarea_id):

    try:
        tarea = Tarea.objects.get(id=tarea_id, usuario=request.user)
    except Tarea.DoesNotExist:
        return Response(
            {'error': 'Tarea no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializador = TareaSerializador(tarea)
        return Response(serializador.data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
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
        tarea.delete()
        return Response(
            {'mensaje': 'Tarea eliminada'},
            status=status.HTTP_200_OK
        )