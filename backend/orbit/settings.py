import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de seguridad
SECRET_KEY = config('SECRET_KEY', default='django-insecure-cambiar-en-produccion')
DEBUG = config('DEBUG', default=True, cast=bool)

# Dominios permitidos
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Base de datos SQLite para Django admin y tablas de Django
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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
    'apps.restablecimiento',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.middlewares.captcha.VerificarCaptchaMiddleware',
]

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:5500', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# reCAPTCHA v2 (vacío => verificación desactivada)
RECAPTCHA_SITE_KEY = config('RECAPTCHA_SITE_KEY', default='')
RECAPTCHA_SECRET_KEY = config('RECAPTCHA_SECRET_KEY', default='')

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

# Idioma y zona horaria
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# Configuración de archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "static/"

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
    default='Orbit <no-responder@orbit.local>',
)

# URL base del frontend para construir el enlace de restablecimiento.
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5500')

# Parámetros del restablecimiento de contraseña.
from datetime import timedelta as _timedelta
RESTABLECIMIENTO_TOKEN_DURACION = _timedelta(
    minutes=config('RESTABLECIMIENTO_TOKEN_MINUTOS', default=30, cast=int)
)
RESTABLECIMIENTO_REINTENTO_SEGUNDOS = config(
    'RESTABLECIMIENTO_REINTENTO_SEGUNDOS', default=120, cast=int
)

# Directorio raíz del frontend (se sirve por Django cuando DEBUG=False)
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Tipo de campo predeterminado para modelos primarios
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
