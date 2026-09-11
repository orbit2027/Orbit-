"""
Punto de entrada ASGI para el proyecto Orbit.
Para servidores de desarrollo y producción con soporte async.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orbit.settings')
application = get_asgi_application()