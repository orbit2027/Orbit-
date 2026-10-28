/**
 * Instancia Axios configurada para el backend de Orbit
 * Interceptor de petición: inyecta JWT automáticamente
 * Manejo de errores de sesión expirada o ausente
 */

// URL base del backend Django.
// En local el frontend se sirve con un servidor estático (Live Server, 5500,
// o el puerto que esté libre) y la API corre aparte en el 8000. Si la página
// la sirve el propio Django (puerto 8000) o estamos en producción, ambos
// comparten origen y basta con '/api/v1'.
const HOSTS_LOCALES = ['localhost', '127.0.0.1', '::1', '[::1]'];
const esHostLocal = HOSTS_LOCALES.includes(window.location.hostname);
const esArchivoLocal = window.location.protocol === 'file:';
const esDesarrolloLocal = esArchivoLocal
    || (esHostLocal && window.location.port !== '8000');
const API_BASE_URL = esDesarrolloLocal
    ? 'http://localhost:8000/api/v1'
    : `${window.location.origin}/api/v1`;

/**
 * Resuelve la ruta hacia el login según la profundidad de la página actual.
 * Las vistas viven en /vistas/ y /vistas/administracion/.
 */
function resolverRutaLogin() {
    const ruta = window.location.pathname;
    if (ruta.includes('/vistas/administracion/')) {
        return '../iniciar-sesion.html';
    }
    if (ruta.includes('/vistas/')) {
        return 'iniciar-sesion.html';
    }
    return 'vistas/iniciar-sesion.html';
}

/**
 * Limpia la sesión y redirige al login.
 * Conserva la página actual en `?volver=` para regresar tras autenticarse
 * (por ejemplo, al abrir una invitación desde el correo sin sesión).
 */
function cerrarSesionYRedirigir() {
    localStorage.removeItem('orbit_token');
    localStorage.removeItem('orbit_usuario');

    let destino = '';
    if (window.location.protocol !== 'file:') {
        destino = window.location.pathname + window.location.search + window.location.hash;
    }
    window.location.href = destino
        ? `${resolverRutaLogin()}?volver=${encodeURIComponent(destino)}`
        : resolverRutaLogin();
}

// Crear instancia de Axios con configuración base
const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Interceptor de petición: inyectar JWT en cada petición
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('orbit_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

/**
 * Indica si la página actual es pública (login, registro, restablecer).
 * En esas páginas un 401/403 es parte del flujo normal y no debe redirigir.
 */
function esPaginaPublica() {
    return /(iniciar-sesion|registrarse|restablecer-contrasena)/.test(
        window.location.pathname
    );
}

/**
 * Detecta si la respuesta indica que la sesión ya no es válida.
 * El backend responde 403 (sin WWW-Authenticate) cuando el JWT expiró,
 * fue revocado o el usuario está desactivado.
 */
function esErrorDeSesion(estado, datos) {
    if (estado === 401) return true;
    if (estado !== 403) return false;
    const codigo = datos?.code;
    const detalle = String(datos?.detail || datos?.mensaje || '');
    return codigo === 'not_authenticated' ||
        codigo === 'authentication_failed' ||
        /token|sesi[oó]n|credencial|autenticad/i.test(detalle);
}

// Interceptor de respuesta: manejar sesión inválida
api.interceptors.response.use(
    (respuesta) => respuesta,
    (error) => {
        const estado = error.response?.status;

        // 401: token expirado o inválido.
        // 403 con código not_authenticated: petición sin credenciales
        // (simplejwt 5.x ya no envía WWW-Authenticate, por eso DRF responde 403).
        // 403 con "Token inválido o expirado": el JWT guardado ya no sirve.
        if (esErrorDeSesion(estado, error.response?.data) && !esPaginaPublica()) {
            cerrarSesionYRedirigir();
        }
        return Promise.reject(error);
    }
);

export default api;
export { API_BASE_URL };