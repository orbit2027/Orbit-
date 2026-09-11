/**
 * rutas.js - Protección de rutas client-side
 * Verifica JWT antes de cargar cada vista protegida
 */

import { estaAutenticado, obtenerUsuario } from './autenticacion.js';

// Rutas que requieren autenticación
const RUTAS_PROTEGIDAS = [
    'tablero-kanban.html',
    'mapa-mental.html',
    'estadisticas.html',
    'panel-admin.html'
];

// Rutas exclusivas para administradores
const RUTAS_ADMIN = [
    'panel-admin.html'
];

// Rutas públicas (no requieren autenticación)
const RUTAS_PUBLICAS = [
    'iniciar-sesion.html',
    'registrarse.html',
    '../index.html'
];

/**
 * Verifica si la ruta actual está protegida
 */
function rutaRequiereAuth(ruta) {
    return RUTAS_PROTEGIDAS.some(r => ruta.includes(r));
}

/**
 * Verifica si la ruta es exclusiva de administrador
 */
function rutaEsAdmin(ruta) {
    return RUTAS_ADMIN.some(r => ruta.includes(r));
}

/**
 * Función principal que se ejecuta al cargar cada página
 * Verifica autenticación y permisos antes de mostrar contenido
 */
function verificarAcceso() {
    const rutaActual = window.location.pathname;

    // Si es ruta pública, permitir acceso
    if (RUTAS_PUBLICAS.some(r => rutaActual.includes(r))) {
        // Si ya está autenticado y va a login/registro, redirigir al tablero
        if (estaAutenticado()) {
            const usuario = obtenerUsuario();
            if (usuario && usuario.rol === 'administrador') {
                window.location.href = '/vistas/administracion/panel-admin.html';
            } else {
                window.location.href = '/vistas/tablero-kanban.html';
            }
        }
        return true;
    }

    // Si es ruta protegida, verificar autenticación
    if (rutaRequiereAuth(rutaActual)) {
        if (!estaAutenticado()) {
            window.location.href = '/vistas/iniciar-sesion.html';
            return false;
        }

        // Si es ruta de admin, verificar rol
        if (rutaEsAdmin(rutaActual)) {
            const usuario = obtenerUsuario();
            if (!usuario || usuario.rol !== 'administrador') {
                window.location.href = '/vistas/tablero-kanban.html';
                return false;
            }
        }
    }

    return true;
}

// Ejecutar verificación al cargar el DOM
document.addEventListener('DOMContentLoaded', verificarAcceso);

// Exportar para uso en otros módulos
export { verificarAcceso, estaAutenticado, obtenerUsuario };
