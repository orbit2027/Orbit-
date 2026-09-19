"""
Enrutador principal de URLs del proyecto Orbit.
Incluye las rutas de todos los módulos del proyecto bajo /api/v1/.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .api_root import api_root
from .vistas_publicas import pagina_privacidad
from apps.captcha.vistas import vista_generar_captcha

urlpatterns = [
    path('admin/', admin.site.urls),
    path('privacidad/', pagina_privacidad, name='privacidad'),

    # API versión 1
    path('api/v1/', api_root, name='api-root'),
    path('api/v1/usuarios/', include('apps.usuarios.rutas')),
    path('api/v1/tareas/', include('apps.tareas.rutas')),
    path('api/v1/mapa-mental/', include('apps.mapa_mental.rutas')),
    path('api/v1/estadisticas/', include('apps.estadisticas.rutas')),
    path('api/v1/administracion/', include('apps.administracion.rutas')),
    path('api/v1/proyectos/', include('apps.proyectos.rutas')),
    path('api/v1/compartir/', include('apps.comparticion.rutas')),
    path('api/v1/restablecimiento/', include('apps.restablecimiento.rutas')),

    # CAPTCHA SVG local (imagen + código de verificación)
    path('api/v1/captcha/', vista_generar_captcha, name='captcha'),

    # Documentación OpenAPI (drf-spectacular)
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
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
