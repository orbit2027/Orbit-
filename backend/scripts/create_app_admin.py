import os
import sys

# Ensure backend package root is on sys.path and Django is configured
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orbit.settings')
import django
django.setup()

from apps.usuarios.modelo import Usuario

def main():
    admin_email = 'admin@orbit.local'
    existing = Usuario.objects(correo=admin_email).first()
    if existing:
        print('ADMIN_EXISTS', existing.correo, existing.rol, existing.activo)
        return

    u = Usuario(
        nombre_completo='App Admin',
        correo=admin_email,
        rol='administrador',
        activo=True
    )
    u.set_contrasena('Admin1234')
    u.save()
    print('ADMIN_CREATED', u.correo, u.rol, u.activo)

if __name__ == '__main__':
    main()