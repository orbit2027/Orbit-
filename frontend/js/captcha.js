/**
 * Widget CAPTCHA SVG local de Orbit (sin servicios externos).
 * La imagen la genera el backend en /api/v1/captcha/ y el código se
 * valida en el middleware con la sesión (el axios ya envía la cookie de
 * sesión gracias a withCredentials).
 *
 * La imagen se descarga por axios (mismo canal HTTP que el resto de la app,
 * con sus cookies/credenciales) y se incrusta como Blob URL. Esto evita los
 * bloqueos que algunos navegadores aplican a la petición directa de una
 * <img> hacia la API (mixed content, cookies de terceros, caché).
 */
import api, { API_BASE_URL } from './api.js';

const ID_IMAGEN = 'captcha-imagen';
const ID_INPUT = 'captcha-input';
const ID_BOTON = 'btn-refrescar-captcha';

let blobUrlActual = null;

async function cargarImagen() {
    const imagen = document.getElementById(ID_IMAGEN);
    if (!imagen) return;
    try {
        const { data: svg } = await api.get('/captcha/', { responseType: 'text' });
        if (blobUrlActual) URL.revokeObjectURL(blobUrlActual);
        const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
        blobUrlActual = URL.createObjectURL(blob);
        imagen.src = blobUrlActual;
    } catch (error) {
        // Plan B: pedir la imagen directamente (sin incrustar el SVG).
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