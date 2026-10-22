"""
Punto de entrada WSGI para el proyecto Orbit.
"""
import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orbit.settings')
application = get_wsgi_application()