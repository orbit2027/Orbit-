/**
 * dialogos.js - Diálogos propios de Orbit.
 */

let dialogoActivo = null;

// Función para escapar texto y prevenir inyección de HTML
function escapar(texto) {
    const div = document.createElement('div');
    div.textContent = texto === null || texto === undefined ? '' : String(texto);
    return div.innerHTML;
}

// Función para crear el overlay del diálogo
function crearOverlay() {
    if (dialogoActivo) dialogoActivo.remove();
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay dialogo-overlay abierto';
    document.body.appendChild(overlay);
    dialogoActivo = overlay;
    return overlay;
}

function configurarCierre(overlay, resolver, valorAceptar, valorCancelar) {
    const cerrar = (valor) => {
        overlay.remove();
        dialogoActivo = null;
        resolver(valor);
    };

    const manejarClick = (e) => {
        const accion = e.target.closest('[data-dialogo]')?.dataset.dialogo;
        if (accion === 'aceptar') cerrar(valorAceptar);
        if (accion === 'cancelar') cerrar(valorCancelar);
        if (e.target === overlay) cerrar(valorCancelar);
    };

    const manejarTeclas = (e) => {
        if (e.key === 'Escape') {
            cerrar(valorCancelar);
            return;
        }
        if (e.key === 'Enter' && valorAceptar !== null) {
            const activo = document.activeElement;
            if (activo && activo.closest('[data-dialogo]')) return;
            if (!activo || activo.tagName !== 'TEXTAREA') {
                e.preventDefault();
                cerrar(valorAceptar);
            }
            return;
        }
        if (e.key === 'Tab') {
            const enfocables = [...overlay.querySelectorAll('button, input, textarea, select')]
                .filter(el => el.offsetParent !== null || el === document.activeElement);
            const idx = enfocables.indexOf(document.activeElement);
            const siguiente = e.shiftKey
                ? enfocables[idx - 1] || enfocables[enfocables.length - 1]
                : enfocables[idx + 1] || enfocables[0];
            if (siguiente) {
                e.preventDefault();
                siguiente.focus();
            }
        }
    };

    overlay.addEventListener('click', manejarClick);
    overlay.addEventListener('keydown', manejarTeclas);
    return cerrar;
}

/**
 * Diálogo de confirmación. Resuelve true/false.
 */
export function confirmar({ titulo = '¿Estás seguro?', mensaje = '', confirmarTexto = 'Confirmar', cancelarTexto = 'Cancelar', peligro = true } = {}) {
    return new Promise((resolve) => {
        const overlay = crearOverlay();
        overlay.innerHTML = `
            <div class="glass-card-strong modal-card dialogo-card" role="dialog" aria-modal="true">
                <h3 class="modal-titulo">${escapar(titulo)}</h3>
                ${mensaje ? `<p class="dialogo-mensaje">${escapar(mensaje)}</p>` : ''}
                <div class="modal-acciones dialogo-acciones">
                    <button type="button" class="btn-secondary" data-dialogo="cancelar">${escapar(cancelarTexto)}</button>
                    <button type="button" class="${peligro ? 'btn-danger-soft' : 'btn-primary'}" data-dialogo="aceptar">${escapar(confirmarTexto)}</button>
                </div>
            </div>`;
        const cerrar = configurarCierre(overlay, resolve, true, false);
        overlay.querySelector('[data-dialogo="aceptar"]').focus();
    });
}

/**
 * Alerta informativa. Resuelve al cerrar.
 */
export function alertar({ titulo = 'Aviso', mensaje = '', aceptarTexto = 'Entendido' } = {}) {
    return new Promise((resolve) => {
        const overlay = crearOverlay();
        overlay.innerHTML = `
            <div class="glass-card-strong modal-card dialogo-card" role="dialog" aria-modal="true">
                <h3 class="modal-titulo">${escapar(titulo)}</h3>
                ${mensaje ? `<p class="dialogo-mensaje">${escapar(mensaje)}</p>` : ''}
                <div class="modal-acciones dialogo-acciones dialogo-acciones--unica">
                    <button type="button" class="btn-primary" data-dialogo="aceptar">${escapar(aceptarTexto)}</button>
                </div>
            </div>`;
        const cerrar = configurarCierre(overlay, resolve, true, true);
        overlay.querySelector('[data-dialogo="aceptar"]').focus();
    });
}

/**
 * Pide un texto (reemplaza prompt). Resuelve string o null si se cancela.
 */
export function preguntarTexto({ titulo = 'Ingresa un valor', mensaje = '', valorInicial = '', placeholder = '', confirmarTexto = 'Aceptar', cancelarTexto = 'Cancelar' } = {}) {
    return new Promise((resolve) => {
        const overlay = crearOverlay();
        overlay.innerHTML = `
            <div class="glass-card-strong modal-card dialogo-card" role="dialog" aria-modal="true">
                <h3 class="modal-titulo">${escapar(titulo)}</h3>
                ${mensaje ? `<p class="dialogo-mensaje">${escapar(mensaje)}</p>` : ''}
                <div class="dialogo-campo">
                    <input class="input-dark" data-dialogo-input value="${escapar(valorInicial)}" placeholder="${escapar(placeholder)}">
                </div>
                <div class="modal-acciones dialogo-acciones">
                    <button type="button" class="btn-secondary" data-dialogo="cancelar">${escapar(cancelarTexto)}</button>
                    <button type="button" class="btn-primary" data-dialogo="aceptar">${escapar(confirmarTexto)}</button>
                </div>
            </div>`;
        const input = overlay.querySelector('[data-dialogo-input]');
        const cerrar = configurarCierre(overlay, resolve, () => input.value, null);
        input.focus();
        input.select();
    });
}