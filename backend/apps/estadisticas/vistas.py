"""
Vistas API para el módulo de estadísticas.
Genera métricas individuales de productividad por usuario.
"""
from datetime import datetime, timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.tareas.modelo import Tarea


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_usuario(request):
    """
    RF-EST-01/02/03: Estadísticas individuales del usuario.
    Retorna contadores por estado, progreso y datos semanales.
    """
    usuario = request.user

    # Contar tareas por estado
    total = Tarea.objects(usuario=usuario).count()
    por_hacer = Tarea.objects(usuario=usuario, estado='por_hacer').count()
    en_progreso = Tarea.objects(usuario=usuario, estado='en_progreso').count()
    completadas = Tarea.objects(usuario=usuario, estado='completado').count()

    # Calcular datos semanales de las últimas semanas
    ahora = datetime.utcnow()
    semanales = []

    for i in range(3, -1, -1):
        inicio_semana = ahora - timedelta(weeks=i + 1)
        fin_semana = ahora - timedelta(weeks=i)

        creadas_semana = Tarea.objects(
            usuario=usuario,
            fecha_creacion__gte=inicio_semana,
            fecha_creacion__lt=fin_semana
        ).count()

        completadas_semana = Tarea.objects(
            usuario=usuario,
            estado='completado',
            fecha_creacion__gte=inicio_semana,
            fecha_creacion__lt=fin_semana
        ).count()

        semanales.append({
            'semana': f'Sem {4 - i}',
            'creadas': creadas_semana,
            'completadas': completadas_semana
        })

    return Response({
        'total': total,
        'por_hacer': por_hacer,
        'en_progreso': en_progreso,
        'completadas': completadas,
        'semanal': semanales
    })
