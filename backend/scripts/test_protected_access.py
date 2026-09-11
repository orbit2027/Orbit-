import os
import sys
import requests

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orbit.settings')
import django
django.setup()


from apps.usuarios.modelo import Usuario
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken

def obtener_token_para(correo):
    usuario = Usuario.objects.filter(correo=correo).first()
    if not usuario:
        print('NO_USER')
        return None
    refresh = RefreshToken.for_user(usuario)
    return str(refresh.access_token)

def probar_acceso(token):
    base = os.environ.get('API_BASE_URL', 'http://127.0.0.1:8000')
    url = f"{base}/api/tareas/"
    headers = {'Authorization': f'Bearer {token}'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print('STATUS', r.status_code)
        try:
            print('BODY', r.json())
        except Exception:
            print('BODY_TEXT', r.text[:500])
    except Exception as e:
        print('REQUEST_ERROR', e)

if __name__ == '__main__':
    correo = 'admin@orbit.local'
    token = obtener_token_para(correo)
    if not token:
        print('FAILED_OBTAIN_TOKEN')
        sys.exit(1)
    print('TOKEN', token[:40] + '...')
    try:
        at = AccessToken(token)
        print('DECODED user_id=', at['user_id'])
    except Exception as e:
        print('ACCESS_TOKEN_DECODE_ERROR', e)
    probar_acceso(token)