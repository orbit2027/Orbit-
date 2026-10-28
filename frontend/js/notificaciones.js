/**
 * notificaciones.js - Panel de notificaciones (campana).
 *
 * Muestra dos bloques reales:
 * - Invitaciones pendientes, con botones para aceptar o rechazar.
 * - Tareas propias o compartidas que vencen en los próximos 3 días.
 *
 * Compartido por tablero, estadísticas, mapa, proyectos y panel admin.
 */

import api from './api.js';
import { mostrarExito, mostrarError } from './utilidades.js';
import { confirmar } from './dialogos.js';
import {
    ETIQUETAS_PERMISO,
    responderInvitacion,
    extraerError,
    tiempoRelativo
} from './invitaciones.js';

function resolverRutaHaciaTablero() {
    const ruta = window.location.pathname;
    if (ruta.includes('/vistas/administracion/')) {
        return '../../vistas/tablero-kanban.html';
    }
    if (ruta.includes('/vistas/')) {
        return 'tablero-kanban.html';
    }
    return 'vistas/tablero-kanban.html';
}

function resolverRutaHaciaInvitaciones() {
    const ruta = window.location.pathname;
    if (ruta.includes('/vistas/administracion/')) {
        return '../../vistas/invitaciones.html';
    }
    if (ruta.includes('/vistas/')) {
        return 'invitaciones.html';
    }
    return 'vistas/invitaciones.html';
}

function aDias(iso) {
    if (!iso) return null;
    const fecha = new Date(iso);
    if (isNaN(fecha.getTime())) return null;
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    fecha.setHours(0, 0, 0, 0);
    return Math.round((fecha - hoy) / 86400000);
}

function formatearDias(dias) {
    if (dias < 0) return `Vence hace ${Math.abs(dias)} día${Math.abs(dias) === 1 ? '' : 's'}`;
    if (dias === 0) return 'Vence hoy';
    if (dias === 1) return 'Vence mañana';
    return `Vence en ${dias} días`;
}

function crearTituloSeccion(texto) {
    const titulo = document.createElement('div');
    titulo.className = 'notif-seccion-titulo';
    titulo.textContent = texto;
    return titulo;
}

function crearFilaInvitacion(invitacion, alResponder) {
    const item = document.createElement('div');
    item.className = 'notificacion-item notificacion-item--invitacion';
    item.title = 'Ir a mis invitaciones';

    const icono = document.createElement('div');
    icono.className = 'notif-icon notif-icon--invitacion';
    icono.innerHTML = '<i class="bi bi-envelope-paper"></i>';

    const contenido = document.createElement('div');
    contenido.className = 'notif-contenido';

    const titulo = document.createElement('div');
    titulo.className = 'notif-titulo';
    titulo.textContent = invitacion.titulo;

    const detalle = document.createElement('div');
    detalle.className = 'notif-detalle';
    const permiso = ETIQUETAS_PERMISO[invitacion.permiso] || 'Puede ver';
    detalle.textContent = `${invitacion.propietario} te invitó · ${permiso}`;

    const fecha = document.createElement('div');
    fecha.className = 'notif-fecha';
    fecha.textContent = tiempoRelativo(invitacion.fecha_compartida);

    const acciones = document.createElement('div');
    acciones.className = 'notif-acciones';
    acciones.addEventListener('click', (e) => e.stopPropagation());

    const aceptar = document.createElement('button');
    aceptar.type = 'button';
    aceptar.className = 'notif-btn notif-btn--aceptar';
    aceptar.textContent = 'Aceptar';
    aceptar.addEventListener('click', () => alResponder(invitacion, true, aceptar));

    const rechazar = document.createElement('button');
    rechazar.type = 'button';
    rechazar.className = 'notif-btn notif-btn--rechazar';
    rechazar.textContent = 'Rechazar';
    rechazar.addEventListener('click', () => alResponder(invitacion, false, rechazar));

    acciones.append(aceptar, rechazar);
    contenido.append(titulo, detalle, fecha, acciones);

    item.append(icono, contenido);
    item.addEventListener('click', () => {
        window.location.href = resolverRutaHaciaInvitaciones();
    });
    return item;
}

function crearFilaTarea(tarea, dias) {
    const item = document.createElement('div');
    item.className = 'notificacion-item';

    const vencida = dias < 0;
    const iconoTipo = tarea.etiqueta ? 'bi-tag' : 'bi-check2-square';
    const color = tarea.color_etiqueta || '#00E5FF';

    item.innerHTML = `
        <div class="notif-icon" style="background: ${color}26; color: ${color}">
            <i class="bi ${iconoTipo}"></i>
        </div>
        <div class="notif-contenido">
            <div class="notif-titulo"></div>
            <div class="notif-detalle${vencida ? ' vencida' : ''}">${formatearDias(dias)}</div>
        </div>`;

    item.querySelector('.notif-titulo').textContent = tarea.titulo;
    item.querySelector('.notif-titulo').title = tarea.titulo;
    item.addEventListener('click', () => {
        window.location.href = resolverRutaHaciaTablero();
    });
    return item;
}

/**
 * Inicializa la campana: carga invitaciones y tareas, y muestra lo relevante.
 */
export async function inicializarNotificaciones() {
    const campana = document.getElementById('campana-notificaciones');
    if (!campana) return;

    const boton = campana;

    // Crear el panel si no existe
    let panel = document.getElementById('panel-notificaciones');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'panel-notificaciones';
        panel.className = 'panel-notificaciones';
        panel.innerHTML = `
            <div class="panel-notificaciones__header">Notificaciones</div>
            <div class="panel-notificaciones__lista" id="lista-notificaciones"></div>`;
        document.body.appendChild(panel);
    }
    const lista = document.getElementById('lista-notificaciones');

    let abierto = false;

    function alternarPanel() {
        abierto = !abierto;
        panel.classList.toggle('visible', abierto);
        if (abierto) cargarNotificaciones();
    }

    boton.addEventListener('click', (e) => {
        e.stopPropagation();
        alternarPanel();
    });

    document.addEventListener('click', (e) => {
        if (panel.classList.contains('visible') && !panel.contains(e.target)) {
            panel.classList.remove('visible');
            abierto = false;
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && panel.classList.contains('visible')) {
            panel.classList.remove('visible');
            abierto = false;
        }
    });

    // Si se responde desde otra vista, refrescar el contador de la campana.
    document.addEventListener('orbit:invitaciones-actualizadas', () => {
        cargarNotificaciones();
    });

    async function alResponderInvitacion(invitacion, aceptar, botonAccion) {
        if (!aceptar) {
            const confirmado = await confirmar({
                titulo: 'Rechazar invitación',
                mensaje: `¿Rechazar la invitación a “${invitacion.titulo}”?`,
                confirmarTexto: 'Rechazar',
                cancelarTexto: 'Volver',
                peligro: true
            });
            if (!confirmado) return;
        }

        const botones = botonAccion.closest('.notif-acciones')?.querySelectorAll('button') || [];
        botones.forEach(b => { b.disabled = true; });
        botonAccion.textContent = aceptar ? 'Aceptando…' : 'Rechazando…';

        try {
            await responderInvitacion(invitacion.token || invitacion.id, aceptar);
            mostrarExito(
                aceptar
                    ? 'Invitación aceptada. Ya tienes acceso.'
                    : 'Invitación rechazada.'
            );
            await cargarNotificaciones();
        } catch (error) {
            mostrarError(extraerError(error, 'No se pudo responder la invitación.'));
            botones.forEach(b => { b.disabled = false; });
            botonAccion.textContent = aceptar ? 'Aceptar' : 'Rechazar';
        }
    }

    async function cargarNotificaciones() {
        lista.innerHTML = '<div class="panel-notificaciones__vacio">Cargando…</div>';

        try {
            const [resTareas, resInvitaciones] = await Promise.allSettled([
                api.get('/tareas/'),
                api.get('/compartir/invitaciones/')
            ]);

            if (resTareas.status === 'rejected' && resInvitaciones.status === 'rejected') {
                throw resTareas.reason;
            }

            const tareas = resTareas.status === 'fulfilled' ? (resTareas.value.data || []) : [];
            const invitaciones = resInvitaciones.status === 'fulfilled' ? (resInvitaciones.value.data || []) : [];
            const falloTareas = resTareas.status === 'rejected';
            const falloInvitaciones = resInvitaciones.status === 'rejected';

            const pendientes = tareas.filter(t => t.estado !== 'completado');
            const conFecha = pendientes
                .map(t => ({ tarea: t, dias: aDias(t.fecha_limite) }))
                .filter(x => x.dias !== null);

            // Vencidas (días <= 0) y próximas 3 días, ordenadas por fecha
            const urgentes = conFecha
                .filter(x => x.dias <= 3)
                .sort((a, b) => a.dias - b.dias);

            const dot = campana.querySelector('.campana-dot');
            const total = urgentes.length + invitaciones.length;
            if (dot) {
                dot.textContent = total;
                dot.classList.toggle('visible', total > 0);
            } else {
                const nuevo = document.createElement('span');
                nuevo.className = 'campana-dot' + (total ? ' visible' : '');
                nuevo.textContent = total;
                campana.appendChild(nuevo);
            }

            lista.innerHTML = '';

            if (falloInvitaciones || falloTareas) {
                const aviso = document.createElement('div');
                aviso.className = 'panel-notificaciones__vacio';
                aviso.textContent = falloInvitaciones && falloTareas
                    ? 'No se pudieron cargar las notificaciones.'
                    : falloInvitaciones
                        ? 'No se pudieron cargar las invitaciones.'
                        : 'No se pudieron cargar las tareas.';
                lista.appendChild(aviso);
            }

            if (!urgentes.length && !invitaciones.length) {
                if (falloInvitaciones || falloTareas) return;
                lista.innerHTML = '<div class="panel-notificaciones__vacio">Todo al día. No tienes invitaciones ni tareas por vencer.</div>';
                return;
            }

            if (invitaciones.length) {
                lista.appendChild(crearTituloSeccion('Invitaciones'));
                invitaciones.forEach(invitacion => {
                    lista.appendChild(crearFilaInvitacion(invitacion, alResponderInvitacion));
                });
            }

            if (urgentes.length) {
                lista.appendChild(crearTituloSeccion('Tareas por vencer'));
                urgentes.forEach(({ tarea, dias }) => {
                    lista.appendChild(crearFilaTarea(tarea, dias));
                });
            }

            if (invitaciones.length) {
                const enlace = document.createElement('a');
                enlace.className = 'panel-notificaciones__enlace';
                enlace.href = resolverRutaHaciaInvitaciones();
                enlace.innerHTML = 'Ver todas las invitaciones <i class="bi bi-arrow-right"></i>';
                lista.appendChild(enlace);
            }
        } catch (error) {
            console.error('Error al cargar notificaciones:', error);
            lista.innerHTML = '<div class="panel-notificaciones__vacio">No se pudieron cargar las notificaciones.</div>';
        }
    }

    // Cargar una vez para reflejar el contador aunque el panel esté cerrado.
    cargarNotificaciones();
}
