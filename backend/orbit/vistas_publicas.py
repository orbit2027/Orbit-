"""Vistas públicas del sitio (páginas no autenticadas)."""
from django.http import HttpResponse


def pagina_privacidad(request):
    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacidad - Orbit</title>
</head>
<body>
    <h1>Hola mundo</h1>
    <p>Esta será la página de privacidad de Orbit.</p>
</body>
</html>"""
    return HttpResponse(html)