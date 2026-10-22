"""
Modelos Django ORM para el mapa mental interactivo.
Define nodos, conexiones y su relación con el módulo de tareas.
"""
from django.db import models
from django.utils import timezone
from apps.usuarios.modelo import Usuario


class NodoMapa(models.Model):
    """
    Modelo que representa un nodo visual en el mapa mental.
    Puede convertirse en tarea del tablero Kanban (RF-MAP-06).
    """
    FORMAS = [
        ('ellipse', 'Elipse'),
        ('round-rectangle', 'Rectángulo redondeado'),
        ('rectangle', 'Rectángulo'),
        ('triangle', 'Triángulo'),
        ('diamond', 'Rombo'),
        ('pentagon', 'Pentágono'),
        ('hexagon', 'Hexágono'),
        ('star', 'Estrella'),
        ('vee', 'En V'),
        ('bar', 'Barra'),
    ]

    ESTILOS = [
        ('cian', 'Cian sólido'),
        ('cian-borde', 'Cian con borde'),
        ('salmon', 'Naranja salmón'),
        ('lila', 'Azul lila'),
    ]

    texto = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default='')
    color = models.CharField(max_length=7, default='#00E5FF', blank=True)
    color_texto = models.CharField(max_length=7, default='#E2E8F0', blank=True)
    forma = models.CharField(max_length=20, choices=FORMAS, default='ellipse')
    estilo = models.CharField(max_length=20, choices=ESTILOS, default='cian')
    posicion_x = models.FloatField(default=0.0)
    posicion_y = models.FloatField(default=0.0)
    asignado = models.CharField(max_length=120, blank=True, default='')
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='nodos_mapa'
    )

    # Control de conversión a tarea
    convertido_en_tarea = models.BooleanField(default=False)
    id_tarea_generada = models.CharField(max_length=50, default='', blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Nodo: {self.texto} (color: {self.color})"


class ConexionNodo(models.Model):
    """
    Modelo que representa una conexión visual entre dos nodos.
    Las conexiones se eliminan automáticamente si se elimina alguno de los nodos.
    """
    nodo_origen = models.ForeignKey(
        NodoMapa, on_delete=models.CASCADE, related_name='conexiones_origen'
    )
    nodo_destino = models.ForeignKey(
        NodoMapa, on_delete=models.CASCADE, related_name='conexiones_destino'
    )
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='conexiones_nodo'
    )

    def __str__(self):
        return f"Conexión: {self.nodo_origen.texto} → {self.nodo_destino.texto}"