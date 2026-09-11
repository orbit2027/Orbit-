/**
 * autenticacion.js - Gestión de autenticación y JWT
 * Maneja login, registro, logout y almacenamiento de tokens
 */

import api from './api.js';

// Claves usadas en localStorage para persistir la sesión
const CLAVE_TOKEN = 'orbit_token';
const CLAVE_USUARIO = 'orbit_usuario';

/**
 * Guarda el token JWT y los datos del usuario en localStorage
 */
function guardarSesion(tokens, usuario) {
    localStorage.setItem(CLAVE_TOKEN, tokens.access);
    localStorage.setItem(CLAVE_USUARIO, JSON.stringify(usuario));
}

/**
 * Elimina la sesión del localStorage
 */
function cerrarSesion() {
    localStorage.removeItem(CLAVE_TOKEN);
    localStorage.removeItem(CLAVE_USUARIO);
}

/**
 * Verifica si hay una sesión activa
 */
function estaAutenticado() {
    return localStorage.getItem(CLAVE_TOKEN) !== null;
}

/**
 * Obtiene el token JWT almacenado
 */
function obtenerToken() {
    return localStorage.getItem(CLAVE_TOKEN);
}

/**
 * Obtiene los datos del usuario almacenados
 */
function obtenerUsuario() {
    const datos = localStorage.getItem(CLAVE_USUARIO);
    try {
        return datos ? JSON.parse(datos) : null;
    } catch {
        return null;
    }
}

/**
 * Resuelve la ruta hacia una vista según la profundidad de la página actual.
 * Necesario porque las páginas viven en /, /vistas/ y /vistas/administracion/.
 */
function resolverRutaVista(nombreArchivo) {
    const ruta = window.location.pathname;
    if (ruta.includes('/vistas/administracion/')) {
        return `../${nombreArchivo}`;
    }
    if (ruta.includes('/vistas/')) {
        return nombreArchivo;
    }
    return `vistas/${nombreArchivo}`;
}

/**
 * RF-USU-01: Registro de nuevo usuario con auto-login.
 * El backend retorna tokens; se guardan para entrar directo al tablero.
 */
async function registrar(nombreCompleto, correo, contrasena, captchaToken) {
    const respuesta = await api.post('/usuarios/registro/', {
        nombre_completo: nombreCompleto,
        correo: correo,
        contrasena: contrasena,
        captcha_token: captchaToken
    });

    guardarSesion(respuesta.data.tokens, respuesta.data.usuario);
    return respuesta.data;
}

/**
 * RF-USU-02: Inicio de sesión.
 * Almacena tokens y datos del usuario.
 */
async function iniciarSesion(correo, contrasena, captchaToken) {
    const respuesta = await api.post('/usuarios/login/', {
        correo: correo,
        contrasena: contrasena,
        captcha_token: captchaToken
    });

    guardarSesion(respuesta.data.tokens, respuesta.data.usuario);
    return respuesta.data;
}

/**
 * RF-USU-06: Cierre de sesión.
 * Limpia localStorage y redirige al login.
 */
function logout() {
    cerrarSesion();
    window.location.href = resolverRutaVista('iniciar-sesion.html');
}

/**
 * RF-USU-03: Obtener perfil del usuario autenticado
 */
async function obtenerPerfil() {
    const respuesta = await api.get('/usuarios/perfil/');
    return respuesta.data;
}

/**
 * RF-USU-04: Editar perfil y sincronizar localStorage
 */
async function editarPerfil(datos) {
    const respuesta = await api.put('/usuarios/editar/', datos);
    localStorage.setItem(CLAVE_USUARIO, JSON.stringify(respuesta.data.usuario));
    return respuesta.data;
}

/**
 * RF-USU-05: Eliminar cuenta con confirmación de contraseña
 */
async function eliminarCuenta(contrasena) {
    const respuesta = await api.delete('/usuarios/eliminar/', {
        data: { contrasena: contrasena }
    });
    cerrarSesion();
    return respuesta.data;
}

/**
 * Redirige según el rol: admin → panel admin, usuario → tablero Kanban
 */
function redirigirSegunRol() {
    const usuario = obtenerUsuario();
    if (!usuario) {
        window.location.href = resolverRutaVista('iniciar-sesion.html');
        return;
    }

    if (usuario.rol === 'administrador') {
        window.location.href = resolverRutaVista('administracion/panel-admin.html');
    } else {
        window.location.href = resolverRutaVista('tablero-kanban.html');
    }
}

export {
    registrar,
    iniciarSesion,
    logout,
    obtenerPerfil,
    editarPerfil,
    eliminarCuenta,
    estaAutenticado,
    obtenerToken,
    obtenerUsuario,
    redirigirSegunRol
};
