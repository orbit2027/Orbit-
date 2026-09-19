/**
 * Widget CAPTCHA SVG local de Orbit (sin servicios externos).
 * La imagen la genera el backend en /api/v1/captcha/ y el código se
 * valida en el middleware con la sesión (el axios ya envía la cookie de
 * sesión gracias a withCredentials).
 */
import { API_BASE_URL } from './api.js';

const ID_IMAGEN = 'captcha-imagen';
const ID_INPUT = 'captcha-input';
const ID_BOTON = 'btn-refrescar-captcha';

function cargarImagen() {
    const imagen = document.getElementById(ID_IMAGEN);
    if (imagen) {
        // El parámetro ?v evita que el navegador sirva la imagen en caché.
        imagen.src = `${API_BASE_URL}/captcha/?v=${Date.now()}`;
    }
}

/** Inicializa el widget: carga la imagen y conecta el botón de refresco. */
export function inicializarCaptcha() {
    const boton = document.getElementById(ID_BOTON);
    if (boton) {
        boton.addEventListener('click', cargarImagen);
    }
    cargarImagen();
}

/** Fuerza un nuevo código de captcha. */
export function refrescarCaptcha() {
    cargarImagen();
}

/** Devuelve el código escrito (mayúsculas, sin espacios). */
export function obtenerCodigoCaptcha() {
    const input = document.getElementById(ID_INPUT);
    return input ? input.value.trim().toUpperCase() : '';
}

/** Limpia el input y pide un código nuevo. */
export function limpiarCaptcha() {
    const input = document.getElementById(ID_INPUT);
    if (input) {
        input.value = '';
    }
    cargarImagen();
}