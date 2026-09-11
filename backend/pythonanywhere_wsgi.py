"""
WSGI auxiliar para PythonAnywhere.

Uso:
1. Crea una Web App tipo "Manual configuration".
2. En el apartado "Code" -> "WSGI configuration file" apunta a este archivo:
   /home/TU_USUARIO/Orbit/backend/pythonanywhere_wsgi.py
3. Asegúrate de que backend/.env exista en tu servidor con ALLOWED_HOSTS
   incluyendo TU_USUARIO.pythonanywhere.com y DEBUG=False.
"""
import os
import sys

# Añade el directorio backend/ al path de Python y lo toma como raíz de trabajo,
# de modo que python-decouple encuentre backend/.env y Django importe "orbit".
RUTA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
sys.path.append(RUTA_PROYECTO)
os.chdir(RUTA_PROYECTO)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orbit.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()