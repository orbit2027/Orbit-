"""
Rutas URL del módulo de compartición.
"""
from django.urls import path
from . import vistas

urlpatterns = [
    path('', vistas.crear_comparticion, name='compartir'),
    path('conmigo/', vistas.compartidos_conmigo, name='compartidos-conmigo'),
    path('invitaciones/', vistas.mis_invitaciones, name='mis-invitaciones'),
    path(
        'invitaciones/<str:referencia>/responder/',
        vistas.responder_invitacion,
        name='responder-invitacion',
    ),
    path(
        'invitaciones/<int:invitacion_id>/reenviar/',
        vistas.reenviar_invitacion,
        name='reenviar-invitacion',
    ),
    path(
        'invitaciones/<int:invitacion_id>/',
        vistas.detalle_invitacion,
        name='detalle-invitacion',
    ),
    path('lista/<str:tipo_objeto>/<str:objeto_id>/',
         vistas.lista_comparticiones, name='lista-comparticiones'),
    path('<str:comparticion_id>/',
         vistas.detalle_comparticion, name='detalle-comparticion'),
]
