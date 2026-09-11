/**
 * utilidades.js - Funciones reutilizables para el frontend
 * Alertas, formateo de fechas y validaciones comunes
 */

/**
 * Muestra una alerta de éxito temporal
 */
function mostrarExito(mensaje) {
    const alerta = document.createElement('div');
    alerta.className = 'alerta alerta-exito';
    alerta.textContent = mensaje;
    document.body.appendChild(alerta);

    setTimeout(() => {
        alerta.remove();
    }, 3000);
}

/**
 * Muestra una alerta de error temporal
 */
function mostrarError(mensaje) {
    const alerta = document.createElement('div');
    alerta.className = 'alerta alerta-error';
    alerta.textContent = mensaje;
    document.body.appendChild(alerta);

    setTimeout(() => {
        alerta.remove();
    }, 4000);
}

/**
 * Muestra una alerta de advertencia temporal
 */
function mostrarAdvertencia(mensaje) {
    const alerta = document.createElement('div');
    alerta.className = 'alerta alerta-advertencia';
    alerta.textContent = mensaje;
    document.body.appendChild(alerta);

    setTimeout(() => {
        alerta.remove();
    }, 3500);
}

/**
 * Formatea una fecha ISO a formato legible
 */
function formatearFecha(fechaISO) {
    if (!fechaISO) return 'Sin fecha';
    const fecha = new Date(fechaISO);
    return fecha.toLocaleDateString('es-MX', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });
}

/**
 * Formatea una fecha ISO con hora
 */
function formatearFechaHora(fechaISO) {
    if (!fechaISO) return 'Sin fecha';
    const fecha = new Date(fechaISO);
    return fecha.toLocaleString('es-MX', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Calcula el tiempo relativo (hace X tiempo)
 */
function tiempoRelativo(fechaISO) {
    if (!fechaISO) return 'Desconocido';
    const fecha = new Date(fechaISO);
    const ahora = new Date();
    const segundos = Math.floor((ahora - fecha) / 1000);

    if (segundos < 60) return 'Ahora mismo';
    if (segundos < 3600) return `Hace ${Math.floor(segundos / 60)} min`;
    if (segundos < 86400) return `Hace ${Math.floor(segundos / 3600)} h`;
    return formatearFecha(fechaISO);
}

/**
 * Valida que un correo tenga formato válido
 */
function validarCorreo(correo) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(correo);
}

/**
 * Valida que una contraseña cumpla requisitos mínimos
 */
function validarContrasena(contrasena) {
    return {
        longitud: contrasena.length >= 8,
        mayuscula: /[A-Z]/.test(contrasena),
        numero: /\d/.test(contrasena)
    };
}

/**
 * Debounce para limitar la frecuencia de ejecución
 */
function debounce(funcion, espera = 300) {
    let temporizador;
    return function ejecutar(...args) {
        clearTimeout(temporizador);
        temporizador = setTimeout(() => funcion.apply(this, args), espera);
    };
}

/**
 * Genera un ID único para elementos temporales
 */
function generarId() {
    return '_' + Math.random().toString(36).substring(2, 11);
}

// Exportar funciones
export {
    mostrarExito,
    mostrarError,
    mostrarAdvertencia,
    formatearFecha,
    formatearFechaHora,
    tiempoRelativo,
    validarCorreo,
    validarContrasena,
    debounce,
    generarId
};