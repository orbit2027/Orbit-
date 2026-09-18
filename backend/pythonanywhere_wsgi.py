"""
WSGI auxiliar para PythonAnywhere.

"""
import os
import sys

# Añade el directorio backend/ al path de Python y lo toma como raíz de trabajo,
# de modo que python-decouple encuentre backend/.env y Django importe "orbit".
RUTA_PROYECTO = os.path.dirname(os.path.abspath(__file__))
sys.path.append(RUTA_PROYECTO)
os.chdir(RUTA_PROYECTO)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orbit.settings')

from django.core.wsgi import get_wsgi_application 

application = get_wsgi_application()