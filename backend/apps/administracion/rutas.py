from django.urls import path
from . import vistas

urlpatterns = [
    path('estadisticas/', vistas.estadisticas_globales, name='estadisticas-globales'),
    path('configuracion/publica/', vistas.configuracion_publica, name='configuracion-publica'),
    path('configuracion/', vistas.configuracion_admin, name='configuracion-admin'),
    path('usuarios/', vistas.listar_usuarios, name='listar-usuarios'),
    path('usuarios/crear/', vistas.crear_usuario, name='crear-usuario'),
    path('usuarios/<str:usuario_id>/', vistas.detalle_usuario, name='detalle-usuario'),
    path('usuarios/<str:usuario_id>/toggle/', vistas.toggle_usuario, name='toggle-usuario'),
    path('contenido/tareas/', vistas.tareas_todas, name='tareas-admin'),
    path('contenido/tareas/<int:tarea_id>/', vistas.moderar_tarea, name='moderar-tarea'),
    path('contenido/proyectos/', vistas.proyectos_todos, name='proyectos-admin'),
    path('contenido/proyectos/<int:proyecto_id>/', vistas.moderar_proyecto, name='moderar-proyecto'),
]
