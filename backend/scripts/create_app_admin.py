import os
import sys
import getpass
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

# Ensure backend package root is on sys.path and Django is configured
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orbit.settings')
import django
django.setup()

from apps.usuarios.modelo import Usuario
from apps.administracion.politica_contrasena import validar_contrasena

def main():
    admin_email = input('Correo del nuevo administrador: ').strip().lower()
    try:
        validate_email(admin_email)
    except ValidationError as error:
        raise SystemExit('Ingresa un correo electrónico válido.') from error

    existing = Usuario.objects.filter(correo=admin_email).first()
    if existing:
        if existing.rol != 'administrador':
            raise SystemExit(
                'Ese correo ya pertenece a una cuenta que no es administradora.'
            )
        print('ADMIN_EXISTS')
        return

    contrasena = getpass.getpass('Contraseña nueva (no se mostrará): ')
    confirmacion = getpass.getpass('Confirma la contraseña: ')
    if contrasena != confirmacion:
        raise SystemExit('Las contraseñas no coinciden.')
    errores = validar_contrasena(contrasena)
    if errores:
        raise SystemExit('\n'.join(errores))

    u = Usuario(
        nombre_completo=input('Nombre del administrador: ').strip(),
        correo=admin_email,
        rol='administrador',
        activo=True
    )
    if not u.nombre_completo:
        raise SystemExit('Ingresa el nombre del administrador.')
    u.set_contrasena(contrasena)
    u.save()
    print('ADMIN_CREATED', u.correo)

if __name__ == '__main__':
    main()