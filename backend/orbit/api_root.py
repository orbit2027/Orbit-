"""
Vista raíz de la API.

Genera el "API root" navegable de Django REST Framework con enlaces
a los endpoints de cada módulo del backend.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """Enlista los endpoints de la API para navegar y probarlos."""
    r = reverse
    return Response({
        'usuarios': {
            'registro': r('registro', request=request, format=format),
            'login': r('login', request=request, format=format),
            'logout': r('logout', request=request, format=format),
            'perfil': r('perfil', request=request, format=format),
            'editar': r('editar-perfil', request=request, format=format),
            'eliminar_cuenta': r('eliminar-cuenta', request=request, format=format),
        },
        'tareas': {
            'lista_tareas': r('lista-tareas', request=request, format=format),
            'detalle_tarea': '/api/tareas/<id>/',
        },
        'mapa_mental': {
            'mapa_completo': r('mapa-completo', request=request, format=format),
            'crear_nodo': r('crear-nodo', request=request, format=format),
            'detalle_nodo': '/api/mapa-mental/nodos/<id>/',
            'convertir_nodo_en_tarea': '/api/mapa-mental/nodos/<id>/convertir-tarea/',
            'crear_conexion': r('crear-conexion', request=request, format=format),
            'eliminar_conexion': '/api/mapa-mental/conexiones/<id>/',
        },
        'proyectos': {
            'lista_proyectos': r('lista-proyectos', request=request, format=format),
            'todos_admin': r('proyectos-todos', request=request, format=format),
            'detalle_proyecto': '/api/proyectos/<id>/',
            'archivar_proyecto': '/api/proyectos/<id>/archivar/',
        },
        'estadisticas': {
            'estadisticas_usuario': r('estadisticas-usuario', request=request, format=format),
        },
        'administracion': {
            'estadisticas_globales': r('estadisticas-globales', request=request, format=format),
            'listar_usuarios': r('listar-usuarios', request=request, format=format),
            'crear_usuario': r('crear-usuario', request=request, format=format),
            'detalle_usuario': '/api/administracion/usuarios/<id>/',
            'toggle_activo': '/api/administracion/usuarios/<id>/toggle/',
        },
    })