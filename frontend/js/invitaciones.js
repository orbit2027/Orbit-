/**
 * invitaciones.js - Utilidades compartidas de invitaciones.
 *
 * Centraliza las llamadas a la API y el formato de fechas, permisos y estados
 * para que el diálogo de compartir, la campana y la página de invitaciones
 * hablen el mismo idioma.
 */
import api from './api.js';

export const ETIQUETAS_PERMISO = {
    ver: 'Puede ver',
    editar: 'Puede editar',
    administrar: 'Puede administrar'
};

const ESTADOS = {
    pendiente: {
        texto: 'Pendiente',
        clase: 'compartir-estado--pendiente',
        icono: 'bi-hourglass-split'
    },
    aceptada: {
        texto: 'Aceptada',
        clase: 'compartir-estado--aceptada',
        icono: 'bi-check-circle'
    },
    rechazada: {
        texto: 'Rechazada',
        clase: 'compartir-estado--rechazada',
        icono: 'bi-x-circle'
    }
};

/** Devuelve texto, clase e icono asociados a un estado de invitación. */
export function etiquetaEstado(estado) {
    return ESTADOS[estado] || ESTADOS.pendiente;
}

/** Primer error legible de una respuesta de la API. */
export function extraerError(error, respaldo = 'No se pudo completar la operación.') {
    const datos = error?.response?.data;
    if (datos?.error) return datos.error;
    if (typeof datos === 'string') return datos;
    const primero = Array.isArray(datos) ? datos[0] : Object.values(datos || {})[0];
    if (Array.isArray(primero)) return primero[0];
    if (typeof primero === 'string') return primero;
    return respaldo;
}

/** Fecha relativa breve en español: "hace 5 min", "ayer", "12 oct 2026". */
export function tiempoRelativo(iso) {
    if (!iso) return '';
    const fecha = new Date(iso);
    if (Number.isNaN(fecha.getTime())) return '';

    const segundos = Math.max(0, Math.round((Date.now() - fecha.getTime()) / 1000));
    if (segundos < 60) return 'hace un momento';

    const minutos = Math.round(segundos / 60);
    if (minutos < 60) return `hace ${minutos} min`;

    const horas = Math.round(minutos / 60);
    if (horas < 24) return `hace ${horas} h`;

    const dias = Math.round(horas / 24);
    if (dias === 1) return 'ayer';
    if (dias < 30) return `hace ${dias} días`;

    return fecha.toLocaleDateString('es', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

/** Invitaciones pendientes dirigidas al correo del usuario autenticado. */
export async function obtenerInvitacionesPendientes() {
    const { data } = await api.get('/compartir/invitaciones/');
    return Array.isArray(data) ? data : [];
}

/**
 * Acepta o rechaza una invitación.
 * `referencia` puede ser el id numérico o el token del correo.
 */
export async function responderInvitacion(referencia, aceptar) {
    const { data } = await api.post(
        `/compartir/invitaciones/${encodeURIComponent(referencia)}/responder/`,
        { aceptar: Boolean(aceptar) }
    );

    document.dispatchEvent(new CustomEvent('orbit:invitaciones-actualizadas', {
        detail: { aceptar: Boolean(aceptar), respuesta: data }
    }));
    if (aceptar) {
        document.dispatchEvent(new CustomEvent('orbit:invitacion-aceptada', {
            detail: { respuesta: data }
        }));
    }
    return data;
}

/** Refresca el contador de invitaciones pendientes del sidebar. */
export async function refrescarBadgeInvitaciones() {
    try {
        const invitaciones = await obtenerInvitacionesPendientes();
        actualizarBadgeInvitaciones(invitaciones.length);
        return invitaciones.length;
    } catch {
        return null;
    }
}

/** Actualiza todos los badges de invitaciones visibles. */
export function actualizarBadgeInvitaciones(total) {
    document.querySelectorAll('[data-badge="invit"]').forEach(badge => {
        badge.textContent = total;
        badge.classList.toggle('visible', total > 0);
    });
}
