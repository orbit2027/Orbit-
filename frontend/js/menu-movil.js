/**
 * menu-movil.js - Menú off-canvas para pantallas móviles.
 * Convierte el sidebar en un panel deslizable con hamburguesa y fondo.
 */

export function inicializarMenuMovil() {
    const sidebar = document.querySelector('.sidebar');
    const topbar = document.querySelector('.topbar');
    if (!sidebar || !topbar) return;

    const boton = document.createElement('button');
    boton.className = 'btn-hamburguesa';
    boton.setAttribute('aria-label', 'Abrir menú');
    boton.innerHTML = '<i class="bi bi-list"></i>';
    topbar.insertBefore(boton, topbar.firstChild);

    const fondo = document.createElement('div');
    fondo.className = 'sidebar-fondo';
    document.body.appendChild(fondo);

    function abrir() {
        sidebar.classList.add('abierto');
        fondo.classList.add('activo');
        document.body.classList.add('menu-abierto');
    }

    function cerrar() {
        sidebar.classList.remove('abierto');
        fondo.classList.remove('activo');
        document.body.classList.remove('menu-abierto');
    }

    boton.addEventListener('click', abrir);
    fondo.addEventListener('click', cerrar);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') cerrar();
    });

    sidebar.querySelectorAll('.sidebar-item, .btn-cerrar-sesion').forEach((el) => {
        el.addEventListener('click', cerrar);
    });
}