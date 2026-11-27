/**
 * Widget CAPTCHA SVG local de Orbit (sin servicios externos).
 *
 * El backend devuelve el SVG y, en la cabecera X-Captcha-Sello, un token
 * firmado con el código y su caducidad. El cliente guarda ese par y lo envía
 * junto a la respuesta escrita. No hay estado en sesión: varias pestañas o
 * peticiones simultáneas no se sobrescriben entre sí.
 */
import api from './api.js';

const ID_IMAGEN = 'captcha-imagen';
const ID_INPUT = 'captcha-input';
const ID_BOTON = 'btn-refrescar-captcha';
const CABECERA_SELLO = 'x-captcha-sello';

let selloActual = '';
let blobUrlActual = null;
let contadorCarga = 0;
let controladorActual = null;

function obtenerSello(headers) {
    if (!headers) return '';
    if (typeof headers.get === 'function') {
        return headers.get(CABECERA_SELLO) || '';
    }
    return headers[CABECERA_SELLO] || '';
}

function mostrarErrorCarga(imagen, mensaje) {
    selloActual = '';
    imagen.style.visibility = 'hidden';

    let aviso = document.getElementById('aviso-captcha');
    if (!aviso) {
        aviso = document.createElement('p');
        aviso.id = 'aviso-captcha';
        aviso.className = 'captcha-proyecto__error';
        aviso.setAttribute('role', 'alert');
        const contenedor = imagen.closest('.captcha-proyecto');
        if (contenedor) contenedor.appendChild(aviso);
    }
    if (aviso) aviso.textContent = mensaje;
}

function limpiarErrorCarga(imagen) {
    imagen.style.visibility = '';
    imagen.alt = 'Código de verificación';
    document.getElementById('aviso-captcha')?.remove();
}

async function cargarImagen() {
    const imagen = document.getElementById(ID_IMAGEN);
    if (!imagen) return;

    // Solo la última petición puede pintar la imagen: descarta respuestas
    // tardías de refrescos anteriores (latencia variable en serverless).
    const numeroCarga = ++contadorCarga;
    if (controladorActual) controladorActual.abort();
    const controlador = new AbortController();
    controladorActual = controlador;
    selloActual = '';

    try {
        const respuesta = await api.get('/captcha/', {
            responseType: 'text',
            signal: controlador.signal,
        });
        if (numeroCarga !== contadorCarga) return;

        const svg = typeof respuesta.data === 'string' ? respuesta.data : '';
        const sello = obtenerSello(respuesta.headers);
        if (!svg.includes('<svg') || !sello) {
            throw new Error('Respuesta de captcha inválida');
        }

        selloActual = sello;
        if (blobUrlActual) URL.revokeObjectURL(blobUrlActual);
        blobUrlActual = URL.createObjectURL(
            new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
        );
        imagen.src = blobUrlActual;
        limpiarErrorCarga(imagen);
    } catch (error) {
        if (error?.code === 'ERR_CANCELED' || numeroCarga !== contadorCarga) return;
        mostrarErrorCarga(
            imagen,
            'No se pudo cargar el captcha. Pulsa el botón de refresco e inténtalo otra vez.'
        );
    }
}

/** Inicializa el widget: carga la imagen y conecta el botón de refresco. */
export function inicializarCaptcha() {
    const boton = document.getElementById(ID_BOTON);
    if (boton && !boton.dataset.captchaInicializado) {
        boton.dataset.captchaInicializado = '1';
        boton.addEventListener('click', refrescarCaptcha);
    }
    cargarImagen();
}

/** Borra la respuesta anterior y pide un código nuevo. */
export function refrescarCaptcha() {
    const input = document.getElementById(ID_INPUT);
    if (input) input.value = '';
    return cargarImagen();
}

/** Alias conservado por compatibilidad. */
export function limpiarCaptcha() {
    return refrescarCaptcha();
}

/**
 * Devuelve el par (sello firmado, respuesta escrita) que espera la API.
 * Devuelve campos vacíos si la imagen no se pudo cargar.
 */
export function obtenerCaptcha() {
    const input = document.getElementById(ID_INPUT);
    return {
        sello: selloActual,
        codigo: input ? input.value.trim().toUpperCase() : '',
    };
}
