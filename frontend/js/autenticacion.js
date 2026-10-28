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
 * Devuelve el destino al que volver tras iniciar sesión o registrarse.
 * Solo acepta rutas relativas del mismo origen (evita redirecciones externas).
 */
function obtenerDestinoVolver() {
    const destino = new URLSearchParams(window.location.search).get('volver');
    if (!destino) return null;
    if (/^[a-z][a-z0-9+.-]*:/i.test(destino) || destino.startsWith('//')) {
        return null;
    }
    return destino;
}

/** Añade `?volver=` a un enlace conservando el destino actual. */
function urlConVolver(ruta) {
    const destino = obtenerDestinoVolver();
    if (!destino) return ruta;
    const separador = ruta.includes('?') ? '&' : '?';
    return `${ruta}${separador}volver=${encodeURIComponent(destino)}`;
}

/**
 * Registro de nuevo usuario con auto-login.
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
 * Inicio de sesión.
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
 * Cierre de sesión.
 * Limpia localStorage y redirige al login.
 * `opciones.cuentaInhabilitada` añade el aviso de cuenta inhabilitada.
 */
function logout(opciones = {}) {
    cerrarSesion();
    const aviso = opciones.cuentaInhabilitada ? '?cuenta=inhabilitada' : '';
    window.location.href =
        `${resolverRutaVista('iniciar-sesion.html')}${aviso}`;
}

/**
 * Obtener perfil del usuario autenticado
 */
async function obtenerPerfil() {
    const respuesta = await api.get('/usuarios/perfil/');
    return respuesta.data;
}

/**
 * Editar perfil y sincronizar localStorage
 */
async function editarPerfil(datos) {
    const respuesta = await api.put('/usuarios/editar/', datos);
    localStorage.setItem(CLAVE_USUARIO, JSON.stringify(respuesta.data.usuario));
    // Si se cambió la contraseña, el backend invalida la sesión anterior y
    // re-emite un par de tokens nuevo: hay que reemplazar el almacenado.
    if (respuesta.data.tokens) {
        guardarSesion(respuesta.data.tokens, respuesta.data.usuario);
    }
    return respuesta.data;
}

/**
 * Eliminar cuenta con confirmación de contraseña
 */
async function eliminarCuenta(contrasena) {
    const respuesta = await api.delete('/usuarios/eliminar/', {
        data: { contrasena: contrasena }
    });
    cerrarSesion();
    return respuesta.data;
}

/**
 * Inhabilitar la cuenta propia (sin borrar datos) con confirmación de
 * contraseña. Al quedar inactiva, la sesión se cierra y se avisa en el login.
 */
async function inhabilitarCuenta(contrasena) {
    const respuesta = await api.post('/usuarios/inhabilitar/', {
        contrasena: contrasena
    });
    logout({ cuentaInhabilitada: true });
    return respuesta.data;
}

/**
 * Redirige según el rol: admin → panel admin, usuario → tablero Kanban.
 * Si la URL trae `?volver=...` se respeta ese destino (por ejemplo, una
 * invitación abierta desde el correo).
 */
function redirigirSegunRol() {
    const volver = obtenerDestinoVolver();
    if (volver) {
        window.location.href = volver;
        return;
    }

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
    inhabilitarCuenta,
    estaAutenticado,
    obtenerToken,
    obtenerUsuario,
    redirigirSegunRol,
    obtenerDestinoVolver,
    urlConVolver
};