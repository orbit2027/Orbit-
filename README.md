# Orbit

Aplicación web con frontend estático, API Django REST Framework, MongoDB.

## Desarrollo local

Desde la carpeta `backend`, ejecuta un único comando para iniciar la API y el
servidor estático del frontend:

```powershell
python run_dev.py
```

Abre `http://localhost:5500` para usar la aplicación. La API queda disponible
en `http://localhost:8000/api/v1/`. Presiona `Ctrl+C` en la terminal para
detener ambos servidores.

## Despliegue en Vercel

El repositorio incluye configuración para desplegar Django como una Vercel
Function y servir las páginas del frontend desde el mismo dominio. En Vercel,
conecta el repositorio y establece **Root Directory** en `.` (raíz del
repositorio), no en `backend`. Vercel detecta Django mediante
`backend/manage.py`; las dependencias están enlazadas desde `requirements.txt`.

Conecta una base de datos PostgreSQL administrada y configura `DATABASE_URL` y
`SECRET_KEY` como variables de entorno de Vercel, disponibles durante el build
y en ejecución. Establece también `DEBUG=False`. No uses SQLite en el
despliegue: el almacenamiento local de las funciones no es persistente. El
script de build aplica las migraciones; verifica que la base de datos sea
accesible durante el build. CAPTCHA queda habilitado automáticamente cuando
`DEBUG=False`. Agrega el dominio personalizado a `ALLOWED_HOSTS` si usas uno.
Configura también `DEFAULT_FROM_EMAIL` y, si habilitas correos,
`EMAIL_BACKEND`, `EMAIL_API_PROVIDER` y `EMAIL_API_KEY`.

En la configuración del proyecto Vercel, deja **Install Command** y **Build
Command** sin sobrescrituras: las dependencias se instalan desde el
`requirements.txt` de la raíz y la migración está declarada en `pyproject.toml`.
No uses `python run_dev.py` como comando de build o inicio de Vercel.