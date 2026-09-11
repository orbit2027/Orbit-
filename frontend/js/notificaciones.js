/**
 * notificaciones.js - Panel de notificaciones (campana).
 * Muestra tareas vencidas y próximas del usuario a partir de datos reales
 * (GET /tareas/). Compartido por tablero, estadísticas, mapa y panel admin.
 */

import api from './api.js';

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

/**
 * Inicializa la campana: carga tareas y muestra las relevantes.
 * Callback `alSeleccionar` recibe (tarea, origen) al hacer clic en una notificación.
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

    (boton || campana).addEventListener('click', (e) => {
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

    async function cargarNotificaciones() {
        try {
            const respuesta = await api.get('/tareas/');
            const tareas = respuesta.data;

            const pendientes = tareas.filter(t => t.estado !== 'completado');
            const conFecha = pendientes
                .map(t => ({ tarea: t, dias: aDias(t.fecha_limite) }))
                .filter(x => x.dias !== null);

            // Vencidas (días <= 0) y próximas 3 días, ordenadas por fecha
            const urgentes = conFecha
                .filter(x => x.dias <= 3)
                .sort((a, b) => a.dias - b.dias);

            const dot = campana.querySelector('.campana-dot');
            if (dot) {
                dot.textContent = urgentes.length;
                dot.classList.toggle('visible', urgentes.length > 0);
            } else {
                const nuevo = document.createElement('span');
                nuevo.className = 'campana-dot' + (urgentes.length ? ' visible' : '');
                nuevo.textContent = urgentes.length;
                campana.appendChild(nuevo);
            }

            lista.innerHTML = '';

            if (!urgentes.length) {
                lista.innerHTML = '<div class="panel-notificaciones__vacio">Todo al día, no hay tareas por vencer.</div>';
                return;
            }

            urgentes.forEach(({ tarea, dias }) => {
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
                        <div class="notif-titulo" title="${tarea.titulo}">${tarea.titulo}</div>
                        <div class="notif-detalle${vencida ? ' vencida' : ''}">${formatearDias(dias)}</div>
                    </div>`;

                item.addEventListener('click', () => {
                    window.location.href = resolverRutaHaciaTablero();
                });
                lista.appendChild(item);
            });
        } catch (error) {
            console.error('Error al cargar notificaciones:', error);
            lista.innerHTML = '<div class="panel-notificaciones__vacio">No se pudieron cargar las notificaciones.</div>';
        }
    }
}