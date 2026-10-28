import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
EN_VERCEL = bool(os.environ.get('VERCEL'))

# Configuración de seguridad
SECRET_KEY = config('SECRET_KEY', default='django-insecure-cambiar-en-produccion')
DEBUG = config(
    'DEBUG',
    default=not EN_VERCEL,
    cast=bool,
)
if not DEBUG and (
    not SECRET_KEY or SECRET_KEY.startswith('django-insecure-')
):
    raise ImproperlyConfigured(
        'Configura una SECRET_KEY segura cuando DEBUG=False.'
    )

# Dominios permitidos
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
VERCEL_HOSTNAMES = (
    os.environ.get('VERCEL_URL'),
    os.environ.get('VERCEL_PROJECT_PRODUCTION_URL'),
)
for hostname in VERCEL_HOSTNAMES:
    if hostname and hostname not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(hostname)

# PostgreSQL en producción; SQLite se conserva para desarrollo local y pruebas.
DATABASE_URL = config('DATABASE_URL', default='')
if EN_VERCEL and not DATABASE_URL:
    raise ImproperlyConfigured(
        'Configura DATABASE_URL en Vercel para usar PostgreSQL persistente.'
    )
DATABASES = {
    'default': (
        dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0 if EN_VERCEL else 600,
            conn_health_checks=True,
            disable_server_side_cursors=EN_VERCEL,
            ssl_require=EN_VERCEL,
        )
        if DATABASE_URL
        else {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    )
}
if EN_VERCEL and DATABASE_URL:
    # Supabase transaction pooler is designed for short-lived serverless
    # connections and does not support prepared statements or server cursors.
    DATABASES['default'].setdefault('OPTIONS', {}).update(
        {'prepare_threshold': None}
    )

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'apps.usuarios',
    'apps.tareas',
    'apps.mapa_mental',
    'apps.estadisticas',
    'apps.administracion',
    'apps.proyectos',
    'apps.comparticion',
    'apps.email',
    'apps.restablecimiento',
    'apps.captcha',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.captcha.middleware.VerificarCaptchaMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:5500', cast=Csv())
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default=','.join(
        f'https://{hostname}'
        for hostname in VERCEL_HOSTNAMES
        if hostname
    ),
    cast=Csv(),
)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CAPTCHA SVG local (sin servicios externos). En producción pon
# CAPTCHA_HABILITADO=True; en DEBUG la verificación se omite (dev local/pruebas).
CAPTCHA_HABILITADO = config(
    'CAPTCHA_HABILITADO',
    default=not DEBUG,
    cast=bool,
)
CAPTCHA_EXPIRACION_MINUTOS = config('CAPTCHA_EXPIRACION_MINUTOS', default=10, cast=int)

# Configuración de REST Framework con JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.middlewares.autenticacion.AutenticacionJWT',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Documentación de la API con drf-spectacular (OpenAPI 3)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Orbit API',
    'DESCRIPTION': (
        'API REST de Orbit: autenticación JWT, tareas, proyectos, mapa mental, '
        'estadísticas, administración y compartición de tareas/proyectos.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
        'displayRequestDuration': True,
    },
}

# Configuración de JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=config('JWT_ACCESS_TOKEN_LIFETIME', default=24, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# Configuración de plantillas (necesaria para Django)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.csrf',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Configuración de URLs
ROOT_URLCONF = 'orbit.urls'
# Vercel detecta Django por `backend/manage.py` y toma el punto de entrada WSGI
# de esta variable; sin ella el build falla con "could not resolve the
# application entrypoint".
WSGI_APPLICATION = 'orbit.wsgi.application'

# Idioma y zona horaria
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# Configuración de archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "static/"
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Correo saliente: configurable por .env. En desarrollo (sin SMTP) Django
# imprime los correos en la consola del servidor (backend de consola).
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='Orbit <orbit.2027pfh@gmail.com>',
)

# Envío por API HTTP (gratuito, sin SMTP): útil en hosts que bloquean el puerto
# 587 (p. ej. PythonAnywhere gratis). Se usa con
# EMAIL_BACKEND=apps.email.backend.EmailBackendAPI
EMAIL_API_PROVIDER = config('EMAIL_API_PROVIDER', default='brevo')
EMAIL_API_KEY = config('EMAIL_API_KEY', default='')

# Aviso por correo en cada inicio de sesión (se puede desactivar con
# AVISO_INICIO_SESION=False).
AVISO_INICIO_SESION = config('AVISO_INICIO_SESION', default=True, cast=bool)

# URL base del frontend para construir el enlace de restablecimiento.
VERCEL_PUBLIC_HOSTNAME = (
    os.environ.get('VERCEL_PROJECT_PRODUCTION_URL')
    or os.environ.get('VERCEL_URL')
)
FRONTEND_URL = config(
    'FRONTEND_URL',
    default=(
        f'https://{VERCEL_PUBLIC_HOSTNAME}'
        if VERCEL_PUBLIC_HOSTNAME else 'http://localhost:5500'
    ),
)

# Parámetros del restablecimiento de contraseña.
from datetime import timedelta as _timedelta
RESTABLECIMIENTO_TOKEN_DURACION = _timedelta(
    minutes=config('RESTABLECIMIENTO_TOKEN_MINUTOS', default=30, cast=int)
)
RESTABLECIMIENTO_REINTENTO_SEGUNDOS = config(
    'RESTABLECIMIENTO_REINTENTO_SEGUNDOS', default=120, cast=int
)

# Directorio raíz del frontend (se sirve por Django cuando DEBUG=False).
# En Vercel el paquete de la función tiene como raíz la carpeta que contiene
# `manage.py` (`backend/`), así que el frontend llega como `backend/frontend`.
# En local se sirve desde la raíz del repositorio.
_CANDIDATOS_FRONTEND = (
    BASE_DIR.parent / "frontend",
    BASE_DIR / "frontend",
)
FRONTEND_DIR = next(
    (ruta for ruta in _CANDIDATOS_FRONTEND if ruta.is_dir()),
    _CANDIDATOS_FRONTEND[-1],
)

# Tipo de campo predeterminado para modelos primarios
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'