"""Configuración de la app de compartición."""
from django.apps import AppConfig


class ComparticionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.comparticion'
    verbose_name = 'Compartición'