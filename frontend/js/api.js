/**
 * Instancia Axios configurada para el backend de Orbit
 * Interceptor de petición: inyecta JWT automáticamente
 * Manejo de errores de sesión expirada o ausente
 */

// URL base del backend Django.
// Si la página se sirve desde el propio Django (mismo origen, p. ej. PythonAnywhere
// o no local), usamos '/api/v1' relativo. Solo en desarrollo local con Live Server
// (puerto 5500) apuntamos al backend en el puerto 8000.
const esDesarrolloLocal = window.location.port === '5500';
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
 * Limpia la sesión y redirige al login
 */
function cerrarSesionYRedirigir() {
    localStorage.removeItem('orbit_token');
    localStorage.removeItem('orbit_usuario');
    window.location.href = resolverRutaLogin();
}

// Crear instancia de Axios con configuración base
const api = axios.create({
    baseURL: API_BASE_URL,
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

// Interceptor de respuesta: manejar sesión inválida
api.interceptors.response.use(
    (respuesta) => respuesta,
    (error) => {
        const estado = error.response?.status;
        const codigo = error.response?.data?.code;

        // 401: token expirado o inválido.
        // 403 con código not_authenticated: petición sin credenciales
        // (simplejwt 5.x ya no envía WWW-Authenticate, por eso DRF responde 403).
        if (estado === 401 || (estado === 403 && codigo === 'not_authenticated')) {
            cerrarSesionYRedirigir();
        }
        return Promise.reject(error);
    }
);

export default api;
