/**
 * sidebar.js - Barra lateral compartida de Orbit.
 *
 * Renderiza el sidebar en `<aside id="app-sidebar">`, y gestiona:
 * - Colapso / expansión (persistido en localStorage).
 * - Tema claro / oscuro (lo aplica en <html data-tema>).
 * - Búsqueda interna de secciones (con atajo Ctrl/Cmd+K).
 * - Estado activo según la URL actual.
 * - Badge de notificaciones urgentes.
 * - Tooltips en modo colapsado.
 * - Comportamiento móvil (panel deslizable con hamburguesa y fondo).
 */
import api from './api.js';
import { obtenerUsuario, logout } from './autenticacion.js';

const CLAVE_TEMA = 'orbit_tema';
const CLAVE_COLAPSADO = 'orbit_sidebar_colapsado';

function estaEnAdmin() {
    return window.location.pathname.includes('/vistas/administracion/');
}

/** Resuelve la ruta a una vista según la profundidad de la página actual. */
function resolverRuta(archivo) {
    if (window.location.pathname.includes('/vistas/')) {
        return estaEnAdmin() ? `../${archivo}` : archivo;
    }
    return `vistas/${archivo}`;
}

function archivoActual() {
    return window.location.pathname.split('/').pop() || 'index.html';
}

function esAdmin(usuario) {
    return usuario?.rol === 'administrador';
}

// Estructura del menú, agrupada por categorías lógicas.
const GRUPOS = [
    {
        titulo: 'Principal',
        items: [
            { etiqueta: 'Tablero', icono: 'bi-kanban', archivo: 'tablero-kanban.html' },
            { etiqueta: 'Mapa mental', icono: 'bi-diagram-3', archivo: 'mapa-mental.html' },
            { etiqueta: 'Estadísticas', icono: 'bi-bar-chart-line', archivo: 'estadisticas.html' },
            { etiqueta: 'Notificaciones', icono: 'bi-bell', accion: 'notificaciones', badge: 'notif' },
        ],
    },
    {
        titulo: 'Gestión',
        items: [
            { etiqueta: 'Proyectos', icono: 'bi-folder2-open', archivo: 'proyectos.html' },
            { etiqueta: 'Perfil', icono: 'bi-person-gear', archivo: 'perfil.html' },
            {
                etiqueta: 'Administración',
                icono: 'bi-shield-lock',
                archivo: 'administracion/panel-admin.html',
                soloAdmin: true,
                badge: 'Admin',
                badgeSuave: true,
                id: 'sidebar-admin',
            },
            {
                etiqueta: 'Cerrar sesión',
                icono: 'bi-box-arrow-left',
                accion: 'logout',
                peligro: true,
                id: 'btn-cerrar-sesion',
            },
        ],
    },
];

function htmlItem(item, activo) {
    const clases = ['sidebar-item'];
    if (activo) clases.push('active');
    if (item.peligro) clases.push('sidebar-item--peligro');

    const id = item.id ? ` id="${item.id}"` : '';
    const destino = item.archivo ? ` data-archivo="${item.archivo}"` : '';
    const accion = item.accion ? ` data-accion="${item.accion}"` : '';

    let badge = '';
    if (item.badge && item.badgeSuave) {
        badge = `<span class="sidebar-item__badge sidebar-item__badge--suave">${item.badge}</span>`;
    } else if (item.badge) {
        badge = `<span class="sidebar-item__badge" data-badge="${item.badge}">0</span>`;
    }

    return `<button class="${clases.join(' ')}"${id}` +
        ` data-tooltip="${item.etiqueta}" data-etiqueta="${item.etiqueta}"` +
        `${destino}${accion}>` +
        `<i class="bi ${item.icono}"></i>` +
        `<span class="sidebar__texto">${item.etiqueta}</span>${badge}</button>`;
}

function render(sidebar) {
    const usuario = obtenerUsuario();
    const nombre = usuario?.nombre_completo || 'Usuario';
    const iniciales = nombre.split(' ').slice(0, 2).map(p => p[0]).join('').toUpperCase();
    const rol = esAdmin(usuario) ? 'Administrador' : 'Usuario';
    const actual = archivoActual();

    const gruposHtml = GRUPOS.map(grupo => {
        const items = grupo.items.filter(i => !i.soloAdmin || esAdmin(usuario));
        const botones = items
            .map(i => htmlItem(i, i.archivo && i.archivo.split('/').pop() === actual))
            .join('');
        return `<div class="sidebar__grupo">` +
            `<span class="sidebar__grupo-titulo">${grupo.titulo}</span>${botones}</div>`;
    }).join('');

    sidebar.innerHTML = `
        <div class="sidebar__inner">
            <header class="sidebar__perfil">
                <div class="sidebar__avatar" id="avatar-usuario">${iniciales}</div>
                <div class="sidebar__perfil-datos">
                    <div class="sidebar__nombre" id="nombre-usuario">${nombre}</div>
                    <div class="sidebar__rol" id="sidebar-rol">${rol}</div>
                </div>
                <button class="sidebar__toggle" id="sidebar-toggle" aria-label="Colapsar menú">
                    <i class="bi bi-chevron-double-left"></i>
                </button>
            </header>

            <div class="sidebar__buscar">
                <i class="bi bi-search"></i>
                <input class="sidebar__buscador" id="sidebar-buscador" type="text"
                       placeholder="Buscar en Orbit" autocomplete="off">
                <kbd class="sidebar__kbd">Ctrl K</kbd>
            </div>

            <nav class="sidebar__nav" id="sidebar-nav">${gruposHtml}</nav>

            <footer class="sidebar__footer">
                <button class="sidebar__control" id="sidebar-tema" data-tooltip="Modo claro">
                    <i class="bi bi-sun"></i>
                </button>
                <button class="sidebar__control" id="sidebar-ajustes" data-tooltip="Perfil">
                    <i class="bi bi-gear"></i>
                </button>
                <button class="sidebar__control sidebar__control--accion" id="sidebar-agregar" data-tooltip="Nueva tarea">
                    <i class="bi bi-plus-lg"></i>
                </button>
                <button class="sidebar__control" id="sidebar-colapsar" data-tooltip="Colapsar">
                    <i class="bi bi-chevron-double-left"></i>
                </button>
            </footer>
        </div>`;
}

function filtrarNav(sidebar, consulta) {
    const q = (consulta || '').trim().toLowerCase();
    sidebar.querySelectorAll('.sidebar__grupo').forEach(grupo => {
        let visibles = 0;
        grupo.querySelectorAll('.sidebar-item').forEach(item => {
            const coincide = !q || (item.dataset.etiqueta || '').toLowerCase().includes(q);
            item.style.display = coincide ? '' : 'none';
            if (coincide) visibles += 1;
        });
        grupo.style.display = visibles ? '' : 'none';
    });
}

function enlazar(sidebar) {
    sidebar.querySelectorAll('.sidebar-item').forEach(item => {
        item.addEventListener('click', () => {
            const accion = item.dataset.accion;
            if (accion === 'logout') {
                logout();
                return;
            }
            if (accion === 'notificaciones') {
                const campana = document.getElementById('campana-notificaciones');
                if (campana) campana.click();
                else window.location.href = resolverRuta('tablero-kanban.html');
                return;
            }
            if (item.dataset.archivo) {
                window.location.href = resolverRuta(item.dataset.archivo);
            }
        });
    });

    const alternarColapso = () => {
        sidebar.classList.toggle('sidebar--colapsado');
        const colapsado = sidebar.classList.contains('sidebar--colapsado');
        localStorage.setItem(CLAVE_COLAPSADO, colapsado ? '1' : '0');
        document.querySelectorAll('.sidebar__tooltip').forEach(t => t.remove());
    };
    document.getElementById('sidebar-toggle')?.addEventListener('click', alternarColapso);
    document.getElementById('sidebar-colapsar')?.addEventListener('click', alternarColapso);

    document.getElementById('sidebar-tema')?.addEventListener('click', () => {
        const nuevo = document.documentElement.dataset.tema === 'claro' ? 'oscuro' : 'claro';
        aplicarTema(nuevo);
    });

    document.getElementById('sidebar-ajustes')?.addEventListener('click', () => {
        window.location.href = resolverRuta('perfil.html');
    });

    document.getElementById('sidebar-agregar')?.addEventListener('click', () => {
        const accion = document.getElementById('fab-nueva-tarea')
            || document.getElementById('btn-nueva-tarea-topbar');
        if (accion) accion.click();
        else window.location.href = resolverRuta('tablero-kanban.html');
    });

    const buscador = document.getElementById('sidebar-buscador');
    if (buscador) {
        buscador.addEventListener('input', () => filtrarNav(sidebar, buscador.value));
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                buscador.focus();
            }
        });
    }
}

function aplicarTema(tema) {
    document.documentElement.dataset.tema = tema;
    localStorage.setItem(CLAVE_TEMA, tema);
    actualizarBotonTema();
}

function actualizarBotonTema() {
    const boton = document.getElementById('sidebar-tema');
    if (!boton) return;
    const claro = document.documentElement.dataset.tema === 'claro';
    boton.innerHTML = claro
        ? '<i class="bi bi-moon-stars"></i>'
        : '<i class="bi bi-sun"></i>';
    boton.dataset.tooltip = claro ? 'Modo oscuro' : 'Modo claro';
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

async function actualizarBadges(sidebar) {
    const badge = sidebar.querySelector('[data-badge="notif"]');
    if (!badge) return;
    try {
        const { data } = await api.get('/tareas/');
        const urgentes = (data || [])
            .filter(t => t.estado !== 'completado')
            .map(t => aDias(t.fecha_limite))
            .filter(d => d !== null && d <= 3).length;
        badge.textContent = urgentes;
        badge.classList.toggle('visible', urgentes > 0);
    } catch {
        // Sin sesión o error de red: el badge permanece oculto.
    }
}

function activarTooltips(sidebar) {
    let tooltip = null;

    const quitar = () => {
        if (tooltip) {
            tooltip.remove();
            tooltip = null;
        }
    };

    sidebar.addEventListener('mouseover', (e) => {
        if (!sidebar.classList.contains('sidebar--colapsado')) return;
        const objetivo = e.target.closest('[data-tooltip]');
        if (!objetivo || (tooltip && tooltip.dataset.origen === objetivo.dataset.tooltip)) return;

        quitar();
        const nodo = document.createElement('div');
        nodo.className = 'sidebar__tooltip';
        nodo.textContent = objetivo.dataset.tooltip;
        nodo.dataset.origen = objetivo.dataset.tooltip;
        document.body.appendChild(nodo);

        const caja = objetivo.getBoundingClientRect();
        const cajaTip = nodo.getBoundingClientRect();
        nodo.style.left = `${caja.right + 12}px`;
        nodo.style.top = `${Math.max(8, caja.top + caja.height / 2 - cajaTip.height / 2)}px`;
        tooltip = nodo;
    });

    sidebar.addEventListener('mouseout', (e) => {
        if (e.target.closest('[data-tooltip]')) quitar();
    });

    window.addEventListener('scroll', quitar, true);
}

function configurarMovil(sidebar) {
    const barra = document.querySelector('.topbar')
        || document.querySelector('.projects__tabs-bar');
    if (!barra || document.querySelector('.sidebar__hamburguesa')) return;

    const boton = document.createElement('button');
    boton.className = 'sidebar__hamburguesa';
    boton.setAttribute('aria-label', 'Abrir menú');
    boton.innerHTML = '<i class="bi bi-list"></i>';
    barra.insertBefore(boton, barra.firstChild);

    const fondo = document.createElement('div');
    fondo.className = 'sidebar-fondo';
    document.body.appendChild(fondo);

    const abrir = () => {
        sidebar.classList.add('abierto');
        fondo.classList.add('activo');
        document.body.classList.add('menu-abierto');
    };
    const cerrar = () => {
        sidebar.classList.remove('abierto');
        fondo.classList.remove('activo');
        document.body.classList.remove('menu-abierto');
    };

    boton.addEventListener('click', abrir);
    fondo.addEventListener('click', cerrar);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') cerrar();
    });
    sidebar.querySelectorAll('.sidebar-item').forEach(el => el.addEventListener('click', cerrar));
}

/**
 * Inicializa la barra lateral. Debe llamarse al inicio del script de cada vista.
 */
function inicializarSidebar() {
    let sidebar = document.getElementById('app-sidebar')
        || document.querySelector('.sidebar');

    if (!sidebar) {
        sidebar = document.createElement('aside');
        sidebar.className = 'sidebar';
        const layout = document.querySelector('.layout-principal');
        if (layout) layout.insertBefore(sidebar, layout.firstChild);
        else document.body.appendChild(sidebar);
    }
    sidebar.id = 'app-sidebar';

    if (localStorage.getItem(CLAVE_COLAPSADO) === '1') {
        sidebar.classList.add('sidebar--colapsado');
    }

    if (!document.documentElement.dataset.tema) {
        document.documentElement.dataset.tema = localStorage.getItem(CLAVE_TEMA) || 'oscuro';
    }

    render(sidebar);
    enlazar(sidebar);
    activarTooltips(sidebar);
    configurarMovil(sidebar);
    actualizarBotonTema();
    actualizarBadges(sidebar);
}

export { inicializarSidebar, aplicarTema };