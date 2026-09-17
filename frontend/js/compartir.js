/**
 * compartir.js - Diálogo para compartir tareas y proyectos por correo.
 * Permite añadir invitados con permiso (ver/editar/administrar),
 * cambiar permisos y quitar accesos. Solo dueños o administradores.
 */
import api from './api.js';
import { mostrarExito, mostrarError, validarCorreo } from './utilidades.js';
import { confirmar } from './dialogos.js';

const ETIQUETAS_PERMISO = {
    ver: 'Puede ver',
    editar: 'Puede editar',
    administrar: 'Administra'
};

let dialogoAbierto = false;

function extraerError(error) {
    const datos = error.response?.data;
    if (datos?.error) return datos.error;
    if (typeof datos === 'string') return datos;
    const primerCampo = Array.isArray(datos) ? datos[0] : Object.values(datos || {})[0];
    if (Array.isArray(primerCampo)) return primerCampo[0];
    if (typeof primerCampo === 'string') return primerCampo;
    return 'No se pudo completar la operación.';
}

function crearSelectPermiso(valor, onchange) {
    const select = document.createElement('select');
    select.className = 'input-dark compartir-permiso-select';
    select.setAttribute('aria-label', 'Permiso');
    Object.keys(ETIQUETAS_PERMISO).forEach(permiso => {
        const opcion = document.createElement('option');
        opcion.value = permiso;
        opcion.textContent = ETIQUETAS_PERMISO[permiso];
        select.appendChild(opcion);
    });
    select.value = valor;
    select.addEventListener('change', onchange);
    return select;
}

async function cargarLista(overlay, contexto) {
    const lista = overlay.querySelector('.compartir-lista');
    lista.innerHTML = '<p class="compartir-vacio">Cargando…</p>';
    try {
        const comparticiones = await api
            .get(`/compartir/lista/${contexto.tipo}/${contexto.objetoId}/`)
            .then(r => r.data);

        if (comparticiones.length === 0) {
            lista.innerHTML = '<p class="compartir-vacio">Aún no has compartido este elemento.</p>';
            return;
        }

        lista.innerHTML = '';
        comparticiones.forEach(comp => {
            const fila = document.createElement('div');
            fila.className = 'compartir-fila';

            const inicial = (comp.nombre || comp.correo || '?').charAt(0).toUpperCase();
            fila.innerHTML = `
                <div class="avatar avatar-solido">${inicial}</div>
                <div class="compartir-datos">
                    <div class="compartir-nombre">${comp.nombre}</div>
                    <div class="compartir-correo">${comp.correo}</div>
                </div>
            `;

            const select = crearSelectPermiso(comp.permiso, async (e) => {
                try {
                    await api.patch(`/compartir/${comp.id}/`, { permiso: e.target.value });
                    mostrarExito('Permiso actualizado.');
                } catch (error) {
                    mostrarError('No se pudo actualizar el permiso.');
                    await cargarLista(overlay, contexto);
                }
            });
            fila.appendChild(select);

            const btnQuitar = document.createElement('button');
            btnQuitar.className = 'compartir-quitar';
            btnQuitar.title = 'Quitar acceso';
            btnQuitar.innerHTML = '<i class="bi bi-x-lg"></i>';
            btnQuitar.addEventListener('click', async () => {
                const confirmado = await confirmar({
                    titulo: 'Quitar acceso',
                    mensaje: `¿Quitar el acceso a ${comp.correo}?`,
                    confirmarTexto: 'Quitar',
                    cancelarTexto: 'Cancelar',
                    peligro: true
                });
                if (!confirmado) return;
                try {
                    await api.delete(`/compartir/${comp.id}/`);
                    mostrarExito('Acceso eliminado.');
                    await cargarLista(overlay, contexto);
                } catch (error) {
                    mostrarError('No se pudo quitar el acceso.');
                }
            });
            fila.appendChild(btnQuitar);

            lista.appendChild(fila);
        });
    } catch (error) {
        lista.innerHTML = '<p class="compartir-vacio">No se pudo cargar la lista.</p>';
    }
}

export function abrirDialogoCompartir({ tipo, objetoId, titulo }) {
    if (dialogoAbierto) return;
    dialogoAbierto = true;

    const contexto = { tipo, objetoId };
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay abierto';
    overlay.innerHTML = `
        <div class="glass-card-strong modal-card compartir-card">
            <h3 class="modal-titulo"><i class="bi bi-people"></i> Compartir</h3>
            <p class="compartir-subtitulo">${titulo || ''}</p>

            <div class="compartir-nuevo">
                <input class="input-dark" type="email" placeholder="correo@ejemplo.com" autocomplete="off">
                <select class="input-dark compartir-permiso-select" id="compartir-permiso-nuevo"></select>
                <button class="btn-primary" id="compartir-enviar"><i class="bi bi-person-plus"></i> Compartir</button>
            </div>

            <div class="compartir-lista"></div>

            <div class="modal-acciones">
                <button class="btn-secondary" id="compartir-cerrar">Cerrar</button>
            </div>
        </div>
    `;

    const selectNuevo = overlay.querySelector('#compartir-permiso-nuevo');
    Object.keys(ETIQUETAS_PERMISO).forEach(permiso => {
        const opcion = document.createElement('option');
        opcion.value = permiso;
        opcion.textContent = ETIQUETAS_PERMISO[permiso];
        selectNuevo.appendChild(opcion);
    });

    function cerrar() {
        overlay.remove();
        dialogoAbierto = false;
        document.removeEventListener('keydown', manejarTeclas);
    }

    function manejarTeclas(e) {
        if (e.key === 'Escape') cerrar();
    }

    overlay.querySelector('#compartir-cerrar').addEventListener('click', cerrar);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) cerrar();
    });
    document.addEventListener('keydown', manejarTeclas);

    overlay.querySelector('#compartir-enviar').addEventListener('click', async (e) => {
        const btn = e.currentTarget;
        const correo = overlay.querySelector('input[type="email"]').value.trim();
        const permiso = selectNuevo.value;

        if (!validarCorreo(correo)) {
            mostrarError('Ingresa un correo válido.');
            return;
        }

        btn.disabled = true;
        try {
            await api.post('/compartir/', {
                correo: correo,
                tipo_objeto: tipo,
                objeto_id: objetoId,
                permiso: permiso
            });
            overlay.querySelector('input[type="email"]').value = '';
            mostrarExito('Elemento compartido.');
            await cargarLista(overlay, contexto);
        } catch (error) {
            mostrarError(extraerError(error));
        } finally {
            btn.disabled = false;
        }
    });

    document.body.appendChild(overlay);
    cargarLista(overlay, contexto);
}

export function crearBotonCompartir({ tipo, objetoId, titulo }) {
    const boton = document.createElement('button');
    boton.className = 'btn-share-tarea';
    boton.title = 'Compartir';
    boton.innerHTML = '<i class="bi bi-people"></i>';
    boton.addEventListener('click', (e) => {
        e.stopPropagation();
        abrirDialogoCompartir({ tipo, objetoId, titulo });
    });
    return boton;
}