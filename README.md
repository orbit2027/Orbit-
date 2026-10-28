# Orbit

Aplicación web con frontend estático y API Django REST Framework. En local usa
SQLite; en producción, PostgreSQL (Supabase).

## Desarrollo local

Desde la carpeta `backend`, ejecuta un único comando para iniciar la API y el
servidor estático del frontend:

```powershell
python run_dev.py
```

Abre `http://localhost:5500` para usar la aplicación. La API queda disponible
en `http://localhost:8000/api/v1/`. Presiona `Ctrl+C` en la terminal para
detener ambos servidores.

## Despliegue en Vercel + Supabase

El despliegue usa **un solo proyecto de Vercel** con **Root Directory =
`backend`**. Django atiende la API (`/api/v1/`), el admin y `/health/`, y además
sirve el frontend estático (`/`, `/vistas/`, `/css/`, `/js/`, `/img/`) cuando
`DEBUG=False`. Al compartir dominio no hay CORS ni que configurar la URL de la
API en el frontend.

La base de datos es **PostgreSQL de Supabase**. No uses SQLite en Vercel: el
almacenamiento local de las funciones no es persistente y los datos se
perderían en cada despliegue.

### 1. Crear la base de datos en Supabase

1. Crea una cuenta y un proyecto en <https://supabase.com> (guarda la
   contraseña de la base de datos que pides al crearlo).
2. Ve a **Project Settings → Database → Connection string** y elige la pestaña
   **Connection pooling** con modo **Transaction** (puerto `6543`).
3. Copia la URI y sustituye `[YOUR-PASSWORD]` por la contraseña real. Debe
   quedar con esta forma:

   ```text
   postgresql://postgres.<referencia>:<contraseña>@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require
   ```

4. Usa siempre el **pooler de transacciones (6543)**, no la conexión directa
   (5432): las funciones de Vercel abren muchas conexiones cortas y la conexión
   directa de Supabase suele ser solo IPv6, por lo que no resuelve desde Vercel.
   `settings.py` ya configura `prepare_threshold=None` y SSL para ese pooler.

### 2. Variables de entorno en Vercel

En **Project → Settings → Environment Variables** (entorno *Production*, y
repite en *Preview* si quieres previsualizaciones funcionales) define:

| Variable | Valor |
| --- | --- |
| `DATABASE_URL` | Cadena del pooler de Supabase (paso 1). Obligatoria. |
| `SECRET_KEY` | Clave larga y aleatoria. Obligatoria con `DEBUG=False`. |
| `DEBUG` | `False` |
| `FRONTEND_URL` | `https://<tu-dominio>` (se usa en los enlaces de invitación y restablecimiento). |
| `EMAIL_BACKEND` | `apps.email.backend.EmailBackendAPI` |
| `EMAIL_API_PROVIDER` | `brevo` |
| `EMAIL_API_KEY` | Tu clave de Brevo. |
| `DEFAULT_FROM_EMAIL` | `Orbit <no-responder@tudominio.com>` |
| `ALLOWED_HOSTS` | Opcional: solo si usas dominio propio, p. ej. `orbit.com,www.orbit.com`. |
| `CSRF_TRUSTED_ORIGINS` | Opcional con dominio propio, p. ej. `https://orbit.com,https://www.orbit.com`. |

Genera la `SECRET_KEY` con:

```powershell
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

`VERCEL_URL` y `VERCEL_PROJECT_PRODUCTION_URL` los inyecta Vercel: se añaden
solos a `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y `FRONTEND_URL` si no los
sobrescribes. CAPTCHA queda habilitado automáticamente con `DEBUG=False`.

### 3. Importar y desplegar

Con la CLI (desde la raíz del repositorio):

```powershell
git add -A
git commit -m "Preparar despliegue en Vercel y Supabase"
git push

npx vercel login
npx vercel link --project orbit   # crea/enlaza el proyecto
npx vercel --prod
```

O desde el panel de Vercel: **Add New → Project**, importa el repositorio y pon
**Root Directory** en `backend`.

Ajustes que **no** debes sobrescribir:

- **Install Command**: se detecta solo (`pip install -r requirements.txt`).
- **Build Command**: lo define `vercel.json` (no lo pongas en el panel).
- **Output Directory**: vacío.
- Framework Preset: Vercel detecta Django por `manage.py` y resuelve el punto de
  entrada desde `WSGI_APPLICATION` en `settings.py`.

`vercel.json` define el build y amplía el tiempo máximo de la función:

```json
"buildCommand": "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python scripts/preparar_frontend_vercel.py"
```

Los comandos se ejecutan dentro de `backend/`. El último copia `frontend/` a
`backend/frontend/` porque Vercel empaqueta la función tomando como raíz
`backend/`; sin esa copia Django responde `404` en `/` y en las vistas. El archivo
`.vercelignore` evita subir `.venv/`, la app de Flutter, `db.sqlite3`, registros y
`.env`.

### 4. Primer despliegue y migraciones

El build aplica las migraciones (`migrate --noinput`), incluida la de
invitaciones, así que la primera vez que despliegues la base queda creada. Si el
build falla con un error de conexión, revisa que `DATABASE_URL` esté disponible
para *Build* y no solo para *Runtime*, y que la contraseña no lleve caracteres
sin codificar (`@`, `#`, `:` → usa la versión URL-encoded).

Si prefieres migrar a mano desde tu equipo:

```powershell
$env:DATABASE_URL = "postgresql://...:6543/postgres?sslmode=require"
python backend/manage.py migrate
```

### 5. Comprobar el despliegue

- `https://<tu-dominio>/health/` debe responder `ok`.
- Abre la app, inicia sesión y prueba crear una tarea y compartirla: la
  invitación solo da acceso cuando la otra persona la acepta.
- Revisa **Deployments → Functions** para ver errores de ejecución.

### Problemas comunes

- **`could not resolve the application entrypoint`**: falta
  `WSGI_APPLICATION` en `settings.py` (ya está definido).
- **`ImproperlyConfigured: Configura DATABASE_URL`**: la variable no está en el
  entorno del build.
- **`password authentication failed`**: contraseña mal copiada o sin
  URL-encode.
- **La base se pausa**: en el plan gratuito Supabase pausa proyectos inactivos;
  entra al panel para reactivarlo o usa un plan de pago.
- **Correos no llegan**: revisa `EMAIL_API_KEY` y que `DEFAULT_FROM_EMAIL`
  coincida con el remitente validado en Brevo.

No uses `python run_dev.py` como comando de build o de inicio en Vercel.