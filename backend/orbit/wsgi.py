"""
Punto de entrada WSGI para el proyecto Orbit.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orbit.settings')
application = get_wsgi_application()