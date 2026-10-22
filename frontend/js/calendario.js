/**
 * calendario.js - Vista de calendario estilo Outlook.
 * Mes (FullCalendar) + panel de agenda del día seleccionado.
 */

import api from '../js/api.js';
import { obtenerUsuario, logout } from '../js/autenticacion.js';
import { inicializarNotificaciones } from '../js/notificaciones.js';
import { alertar } from '../js/dialogos.js';
import { inicializarSidebar } from '../js/sidebar.js';

inicializarSidebar();

const COLORES_ETIQUETA = {
    'Urgente': '#FF4D4D',
    'Personal': '#A78BFA',
    'Trabajo': '#00E5FF',
    'Estudio': '#F59E0B',
    'Hogar': '#00C48C'
};

const ESTADOS = {
    por_hacer: { texto: 'Por hacer', color: '#64748B' },
    en_progreso: { texto: 'En progreso', color: '#F59E0B' },
    completado: { texto: 'Completada', color: '#00C48C' }
};

let tareas = [];
let diaSeleccionado = null;
let etiquetaSeleccionada = 'Trabajo';
let calendario = null;

const modal = document.getElementById('modal-tarea');

// ═══════════ DATOS DEL USUARIO ═══════════
const usuario = obtenerUsuario();
if (usuario) {
    const iniciales = usuario.nombre_completo.split(' ').slice(0, 2).map(p => p[0]).join('').toUpperCase();
    document.getElementById('avatar-usuario').textContent = iniciales;
    document.getElementById('avatar-topbar').textContent = iniciales;
    document.getElementById('nombre-usuario').textContent = usuario.nombre_completo;
}

// ═══════════ UTILIDADES DE FECHA ═══════════
function hoyISO() {
    const hoy = new Date();
    return aISO(hoy);
}

function aISO(fecha) {
    const anio = fecha.getFullYear();
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const dia = String(fecha.getDate()).padStart(2, '0');
    return `${anio}-${mes}-${dia}`;
}

function formatearFechaLarga(iso) {
    const [anio, mes, dia] = iso.split('-').map(Number);
    const fecha = new Date(anio, mes - 1, dia);
    return fecha.toLocaleDateString('es-ES', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });
}

// ═══════════ CALENDARIO (FULLCALENDAR) ═══════════
function inicializarCalendario() {
    const el = document.getElementById('calendario-mes');
    calendario = new FullCalendar.Calendar(el, {
        initialView: 'dayGridMonth',
        firstDay: 1,
        height: 'auto',
        headerToolbar: false,
        dayMaxEvents: 3,
        fixedWeekCount: false,
        locale: 'es',
        buttonText: { today: 'Hoy' },
        dateClick: (info) => seleccionarDia(info.dateStr),
        eventClick: (info) => {
            info.jsEvent.preventDefault();
            abrirEditorTarea(info.event.id);
        },
        events: construirEventos
    });
    calendario.render();
}

function construirEventos(info, exito) {
    const eventos = tareas
        .filter(t => t.fecha_limite)
        .map(t => {
            const color = COLORES_ETIQUETA[t.etiqueta] || '#00E5FF';
            return {
                id: t.id,
                title: t.titulo,
                start: t.fecha_limite,
                allDay: true,
                backgroundColor: `${color}26`,
                borderColor: color,
                textColor: document.documentElement.dataset.tema === 'claro' ? '#0F172A' : '#E2E8F0',
                classNames: t.estado === 'completado' ? ['fc-evento-completado'] : []
            };
        });
    exito(eventos);
}

// ═══════════ SELECCIÓN DE DÍA + AGENDA ═══════════
function seleccionarDia(iso) {
    diaSeleccionado = iso;

    document.querySelectorAll('#calendario-mes .fc-day-selected')
        .forEach(celda => celda.classList.remove('fc-day-selected'));

    document.querySelectorAll(`#calendario-mes .fc-daygrid-day[data-date="${iso}"]`)
        .forEach(celda => celda.classList.add('fc-day-selected'));

    renderizarAgenda();
}

function tareasDelDia(iso) {
    return tareas
        .filter(t => t.fecha_limite === iso)
        .sort((a, b) => (a.estado === 'completado') - (b.estado === 'completado'));
}

function renderizarAgenda() {
    const tituloFecha = document.getElementById('agenda-fecha');
    const resumen = document.getElementById('agenda-resumen');
    const lista = document.getElementById('agenda-lista');
    const btnAgregar = document.getElementById('agenda-agregar-tarea');

    lista.innerHTML = '';

    if (!diaSeleccionado) {
        tituloFecha.textContent = 'Selecciona un día';
        resumen.textContent = 'Las tareas con fecha límite aparecerán aquí';
        btnAgregar.style.display = 'none';
        return;
    }

    tituloFecha.textContent = formatearFechaLarga(diaSeleccionado);
    const delDia = tareasDelDia(diaSeleccionado);
    const completadas = delDia.filter(t => t.estado === 'completado').length;
    resumen.textContent = delDia.length
        ? `${delDia.length} tarea(s) · ${completadas} completada(s)`
        : 'Sin tareas para este día';
    btnAgregar.style.display = 'flex';

    if (!delDia.length) {
        const vacio = document.createElement('div');
        vacio.className = 'calendario__agenda-vacio';
        vacio.textContent = 'No hay tareas con fecha límite este día';
        lista.appendChild(vacio);
        return;
    }

    delDia.forEach(tarea => lista.appendChild(crearItemAgenda(tarea)));
}

function crearItemAgenda(tarea) {
    const color = COLORES_ETIQUETA[tarea.etiqueta] || '#00E5FF';
    const estado = ESTADOS[tarea.estado] || ESTADOS.por_hacer;

    const item = document.createElement('div');
    item.className = 'calendario__agenda-item';
    item.style.borderLeftColor = color;

    const completadaClase = tarea.estado === 'completado'
        ? ' calendario__agenda-item-titulo--completada' : '';

    item.innerHTML = `
        <div class="calendario__agenda-item-info">
            <div class="calendario__agenda-item-titulo${completadaClase}">${escapar(tarea.titulo)}</div>
            ${tarea.descripcion ? `<div class="calendario__agenda-item-desc">${escapar(tarea.descripcion)}</div>` : ''}
            <div class="calendario__agenda-item-pie">
                <span class="calendario__agenda-estado" style="background:${estado.color}22; color:${estado.color};">${estado.texto}</span>
                ${tarea.etiqueta ? `<span style="font-size:11px; color:${color}; font-weight:600;">${escapar(tarea.etiqueta)}</span>` : ''}
            </div>
        </div>`;

    item.addEventListener('click', () => abrirEditorTarea(tarea.id));
    return item;
}

function escapar(texto) {
    const div = document.createElement('div');
    div.textContent = texto === null || texto === undefined ? '' : String(texto);
    return div.innerHTML;
}

// ═══════════ CARGA DE TAREAS ═══════════
async function cargarTareas() {
    try {
        const respuesta = await api.get('/tareas/');
        tareas = respuesta.data.map(t => ({ ...t, etiqueta: t.etiqueta || 'Trabajo' }));
        if (calendario) calendario.refetchEvents();
        renderizarAgenda();
    } catch (error) {
        console.error('Error al cargar tareas:', error);
    }
}

// ═══════════ NAVEGACIÓN DEL MES ═══════════
document.getElementById('cal-anterior').addEventListener('click', () => calendario.prev());
document.getElementById('cal-siguiente').addEventListener('click', () => calendario.next());
document.getElementById('cal-hoy').addEventListener('click', () => {
    calendario.today();
    seleccionarDia(hoyISO());
});

// ═══════════ MODAL CREAR / EDITAR TAREA ═══════════
let tareaEditandoId = null;

function construirOpcionesEtiqueta() {
    const contenedor = document.getElementById('opciones-etiqueta-modal');
    contenedor.innerHTML = '';
    Object.keys(COLORES_ETIQUETA).forEach(etiqueta => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'pill';
        btn.textContent = etiqueta;
        btn.dataset.etiqueta = etiqueta;
        btn.addEventListener('click', () => seleccionarEtiqueta(etiqueta));
        contenedor.appendChild(btn);
    });
    seleccionarEtiqueta('Trabajo');
}

function seleccionarEtiqueta(etiqueta) {
    etiquetaSeleccionada = etiqueta;
    const color = COLORES_ETIQUETA[etiqueta];
    document.querySelectorAll('#opciones-etiqueta-modal .pill').forEach(btn => {
        const activo = btn.dataset.etiqueta === etiqueta;
        const c = COLORES_ETIQUETA[btn.dataset.etiqueta];
        btn.style.background = activo ? `${c}20` : 'rgba(255,255,255,0.04)';
        btn.style.color = activo ? c : 'var(--color-terciario)';
        btn.style.border = `1px solid ${activo ? c + '60' : 'rgba(100,116,139,0.3)'}`;
    });
}

function abrirNuevaTarea(fecha) {
    tareaEditandoId = null;
    document.getElementById('modal-tarea-titulo').textContent = 'Nueva tarea';
    document.getElementById('btn-guardar-tarea').textContent = 'Crear tarea';
    document.getElementById('tarea-titulo').value = '';
    document.getElementById('tarea-descripcion').value = '';
    document.getElementById('tarea-fecha').value = fecha || diaSeleccionado || '';
    seleccionarEtiqueta('Trabajo');
    modal.style.display = 'flex';
    document.getElementById('tarea-titulo').focus();
}

function abrirEditorTarea(id) {
    const tarea = tareas.find(t => String(t.id) === String(id));
    if (!tarea) return;
    tareaEditandoId = id;
    document.getElementById('modal-tarea-titulo').textContent = 'Editar tarea';
    document.getElementById('btn-guardar-tarea').textContent = 'Guardar cambios';
    document.getElementById('tarea-titulo').value = tarea.titulo;
    document.getElementById('tarea-descripcion').value = tarea.descripcion || '';
    document.getElementById('tarea-fecha').value = tarea.fecha_limite || '';
    seleccionarEtiqueta(tarea.etiqueta in COLORES_ETIQUETA ? tarea.etiqueta : 'Trabajo');
    modal.style.display = 'flex';
    document.getElementById('tarea-titulo').focus();
}

function cerrarModal() {
    modal.style.display = 'none';
    tareaEditandoId = null;
}

document.getElementById('btn-nueva-tarea-calendario').addEventListener('click',
    () => abrirNuevaTarea(diaSeleccionado));
document.getElementById('agenda-agregar-tarea').addEventListener('click',
    () => abrirNuevaTarea(diaSeleccionado));
document.getElementById('btn-cancelar-tarea').addEventListener('click', cerrarModal);
modal.addEventListener('click', (e) => { if (e.target === modal) cerrarModal(); });

document.getElementById('btn-guardar-tarea').addEventListener('click', async () => {
    const titulo = document.getElementById('tarea-titulo').value.trim();
    const descripcion = document.getElementById('tarea-descripcion').value.trim();
    const fecha = document.getElementById('tarea-fecha').value;

    if (!titulo) {
        alertar({ titulo: 'Falta el título', mensaje: 'Escribe un título para la tarea.' });
        return;
    }

    const datos = {
        titulo,
        descripcion,
        etiqueta: etiquetaSeleccionada,
        color_etiqueta: COLORES_ETIQUETA[etiquetaSeleccionada],
        fecha_limite: fecha || null
    };

    try {
        if (tareaEditandoId) {
            await api.patch(`/tareas/${tareaEditandoId}/`, datos);
        } else {
            datos.estado = 'por_hacer';
            await api.post('/tareas/', datos);
        }
        cerrarModal();
        if (fecha) seleccionarDia(fecha);
        await cargarTareas();
    } catch (error) {
        console.error('Error al guardar tarea:', error);
        alertar({ titulo: 'Error', mensaje: 'No se pudo guardar la tarea. Inténtalo de nuevo.' });
    }
});

// ═══════════ INICIO ═══════════
document.getElementById('btn-cerrar-sesion').addEventListener('click', logout);

construirOpcionesEtiqueta();
inicializarNotificaciones();
inicializarCalendario();
seleccionarDia(hoyISO());
cargarTareas();
