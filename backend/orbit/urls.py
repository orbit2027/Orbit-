"""
Enrutador principal de URLs del proyecto Orbit.
Incluye las rutas de todos los módulos del proyecto.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path

from .api_root import api_root

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/usuarios/', include('apps.usuarios.rutas')),
    path('api/tareas/', include('apps.tareas.rutas')),
    path('api/mapa-mental/', include('apps.mapa_mental.rutas')),
    path('api/estadisticas/', include('apps.estadisticas.rutas')),
    path('api/administracion/', include('apps.administracion.rutas')),
    path('api/proyectos/', include('apps.proyectos.rutas')),
]

# En producción (DEBUG=False) Django sirve además el frontend estático,
# de modo que NO hacen falta dos servidores/puertos (clave para PythonAnywhere,
# que solo ejecuta un proceso WSGI por web app). En local mantenemos la
# separación frontend(5500) / backend(8000), por eso aquí se omite.
if not settings.DEBUG:
    from django.views.static import serve
    urlpatterns += [
        re_path(r'^(?P<path>vistas/(?:.*/)?[\w\-]+\.html)$', serve,
                {'document_root': str(settings.FRONTEND_DIR)}, name='servir-vistas'),
        re_path(r'^(?P<path>(?:css|js|img)/.*)$', serve,
                {'document_root': str(settings.FRONTEND_DIR)}, name='servir-estaticos-frontend'),
        re_path(r'^$', serve, {'document_root': str(settings.FRONTEND_DIR),
                               'path': 'index.html'}, name='servir-index'),
    ]