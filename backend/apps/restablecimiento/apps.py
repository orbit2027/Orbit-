"""Configuración de la app de restablecimiento de contraseña."""
from django.apps import AppConfig


class RestablecimientoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.restablecimiento'
    verbose_name = 'Restablecimiento de contraseña'
    models_module = 'apps.restablecimiento.modelo'