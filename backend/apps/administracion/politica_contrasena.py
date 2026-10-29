import re

from .models import obtener_configuracion


def obtener_politica_contrasena():
    configuracion = obtener_configuracion()
    return {
        'longitud_minima': configuracion.longitud_minima_contrasena,
        'mayuscula_requerida': configuracion.exigir_mayuscula,
        'numero_requerido': configuracion.exigir_numero,
    }


def validar_contrasena(contrasena):
    politica = obtener_politica_contrasena()
    errores = []

    if len(contrasena) < politica['longitud_minima']:
        errores.append(
            f"La contraseña debe tener al menos "
            f"{politica['longitud_minima']} caracteres."
        )
    if politica['mayuscula_requerida'] and not any(
        re.search(r'[A-Z]', caracter) for caracter in contrasena
    ):
        errores.append('La contraseña debe contener al menos una mayúscula.')
    if politica['numero_requerido'] and not any(
        re.search(r'\d', caracter) for caracter in contrasena
    ):
        errores.append('La contraseña debe contener al menos un número.')

    return errores
