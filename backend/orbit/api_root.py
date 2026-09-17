"""
Vista raíz de la API.

Genera el "API root" navegable de Django REST Framework con enlaces
a los endpoints de cada módulo del backend.
"""
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from drf_spectacular.utils import extend_schema


class ApiRootSerializador(serializers.Serializer):
    """Raíz navegable de la API v1."""
    usuarios = serializers.DictField(child=serializers.CharField())
    tareas = serializers.DictField(child=serializers.CharField())
    mapa_mental = serializers.DictField(child=serializers.CharField())
    proyectos = serializers.DictField(child=serializers.CharField())
    estadisticas = serializers.DictField(child=serializers.CharField())
    administracion = serializers.DictField(child=serializers.CharField())
    documentacion = serializers.DictField(child=serializers.CharField())


@extend_schema(
    request=None,
    responses={200: ApiRootSerializador},
)
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
            'detalle_tarea': '/api/v1/tareas/<id>/',
        },
        'mapa_mental': {
            'mapa_completo': r('mapa-completo', request=request, format=format),
            'crear_nodo': r('crear-nodo', request=request, format=format),
            'detalle_nodo': '/api/v1/mapa-mental/nodos/<id>/',
            'convertir_nodo_en_tarea': '/api/v1/mapa-mental/nodos/<id>/convertir-tarea/',
            'crear_conexion': r('crear-conexion', request=request, format=format),
            'eliminar_conexion': '/api/v1/mapa-mental/conexiones/<id>/',
        },
        'proyectos': {
            'lista_proyectos': r('lista-proyectos', request=request, format=format),
            'todos_admin': r('proyectos-todos', request=request, format=format),
            'detalle_proyecto': '/api/v1/proyectos/<id>/',
            'archivar_proyecto': '/api/v1/proyectos/<id>/archivar/',
        },
        'estadisticas': {
            'estadisticas_usuario': r('estadisticas-usuario', request=request, format=format),
        },
        'administracion': {
            'estadisticas_globales': r('estadisticas-globales', request=request, format=format),
            'listar_usuarios': r('listar-usuarios', request=request, format=format),
            'crear_usuario': r('crear-usuario', request=request, format=format),
            'detalle_usuario': '/api/v1/administracion/usuarios/<id>/',
            'toggle_activo': '/api/v1/administracion/usuarios/<id>/toggle/',
        },
        'documentacion': {
            'schema_openapi': r('schema', request=request, format=format),
            'swagger_ui': r('swagger-ui', request=request, format=format),
            'redoc': r('redoc', request=request, format=format),
        },
    })