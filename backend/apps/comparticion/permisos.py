"""
Utilidades de permisos para objetos compartidos.
Centralizan la jerarquía ver < editar < administrar.
"""
from .modelo import Comparticion

NIVELES = {'ver': 1, 'editar': 2, 'administrar': 3}

def por_objeto(usuario, tipo_objeto, objeto_id):
    """Devuelve la Comparticion del usuario sobre el objeto o None."""
    return Comparticion.objects.filter(
        compartido_con=usuario,
        tipo_objeto=tipo_objeto,
        objeto_id=objeto_id,
    ).first()


def nivel_sobre_proyecto(usuario, proyecto):
    """Permiso del usuario sobre un proyecto (el dueño administra)."""
    if proyecto.usuario_id == usuario.id:
        return 'administrar'
    comparticion = por_objeto(usuario, 'proyecto', str(proyecto.id))
    return comparticion.permiso if comparticion else None

def nivel_sobre_tarea(usuario, tarea):
    """Permiso del usuario sobre una tarea (incluye proyectos compartidos)."""
    if tarea.usuario_id == usuario.id:
        return 'administrar'
    comparticion = por_objeto(usuario, 'tarea', str(tarea.id))
    if comparticion:
        return comparticion.permiso
    if tarea.proyecto:
        comparticion_proyecto = por_objeto(usuario, 'proyecto', tarea.proyecto)
        if comparticion_proyecto:
            return comparticion_proyecto.permiso
    return None

def _supera(nivel, minimo):
    return nivel is not None and NIVELES[nivel] >= NIVELES[minimo]


def puede_ver(nivel):
    return _supera(nivel, 'ver')


def puede_editar(nivel):
    return _supera(nivel, 'editar')


def puede_administrar(nivel):
    return _supera(nivel, 'administrar')