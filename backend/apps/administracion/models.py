from django.db import models


class ConfiguracionAplicacion(models.Model):
    aviso_global = models.CharField(max_length=500, blank=True, default='')
    mantenimiento_activo = models.BooleanField(default=False)
    mensaje_mantenimiento = models.CharField(
        max_length=500,
        default='Orbit está en mantenimiento. Inténtalo más tarde.',
    )
    longitud_minima_contrasena = models.PositiveSmallIntegerField(default=8)
    exigir_mayuscula = models.BooleanField(default=True)
    exigir_numero = models.BooleanField(default=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'configuración de la aplicación'
        verbose_name_plural = 'configuración de la aplicación'

    def __str__(self):
        return 'Configuración de Orbit'


def obtener_configuracion():
    configuracion, _ = ConfiguracionAplicacion.objects.get_or_create(pk=1)
    return configuracion
