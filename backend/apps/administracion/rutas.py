from django.urls import path
from . import vistas

urlpatterns = [
    path('estadisticas/', vistas.estadisticas_globales, name='estadisticas-globales'),
    path('usuarios/', vistas.listar_usuarios, name='listar-usuarios'),
    path('usuarios/crear/', vistas.crear_usuario, name='crear-usuario'),
    path('usuarios/<str:usuario_id>/', vistas.detalle_usuario, name='detalle-usuario'),
    path('usuarios/<str:usuario_id>/toggle/',vistas.toggle_usuario, name='toggle-usuario'),
]
