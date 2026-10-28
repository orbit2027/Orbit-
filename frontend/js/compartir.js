/**
 * compartir.js - Diálogo para compartir tareas y proyectos por correo.
 *
 * Enviar una invitación NO da acceso inmediato: la persona invitada recibe un
 * correo y debe aceptarlo. Aquí se muestran tanto los accesos aceptados como
 * las invitaciones pendientes o rechazadas, con acciones para cambiar el
 * permiso, reenviar o cancelar. Solo dueños o administradores.
 */
import api from './api.js';
import { mostrarExito, mostrarError, validarCorreo } from './utilidades.js';
import { confirmar } from './dialogos.js';
import {
    ETIQUETAS_PERMISO,
    etiquetaEstado,
    extraerError,
    tiempoRelativo
} from './invitaciones.js';

let dialogoAbierto = false;

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

function crearBotonIcono({ icono, titulo, clase, onClick }) {
    const boton = document.createElement('button');
    boton.type = 'button';
    boton.className = `compartir-accion ${clase || ''}`.trim();
    boton.title = titulo;
    boton.setAttribute('aria-label', titulo);
    boton.innerHTML = `<i class="bi ${icono}"></i>`;
    boton.addEventListener('click', onClick);
    return boton;
}

function rutaDeRegistro(registro) {
    return registro.origen === 'comparticion'
        ? `/compartir/${registro.id}/`
        : `/compartir/invitaciones/${registro.id}/`;
}

function crearFila(registro, overlay, contexto) {
    const fila = document.createElement('div');
    fila.className = 'compartir-fila';
    if (registro.estado === 'rechazada') fila.classList.add('compartir-fila--rechazada');

    const avatar = document.createElement('div');
    avatar.className = 'avatar avatar-solido compartir-avatar';
    avatar.textContent = (registro.nombre || registro.correo || '?')
        .trim().charAt(0).toUpperCase();

    const datos = document.createElement('div');
    datos.className = 'compartir-datos';

    const linea = document.createElement('div');
    linea.className = 'compartir-nombre-linea';

    const nombre = document.createElement('span');
    nombre.className = 'compartir-nombre';
    nombre.textContent = registro.nombre || registro.correo;

    const estado = etiquetaEstado(registro.estado);
    const badge = document.createElement('span');
    badge.className = `compartir-estado ${estado.clase}`;
    badge.innerHTML = `<i class="bi ${estado.icono}"></i>`;
    badge.appendChild(document.createTextNode(estado.texto));
    badge.title = registro.fecha_compartida
        ? `${estado.texto} · ${tiempoRelativo(registro.fecha_compartida)}`
        : estado.texto;

    linea.append(nombre, badge);
    datos.appendChild(linea);

    const correo = document.createElement('div');
    correo.className = 'compartir-correo';
    correo.textContent = registro.origen === 'comparticion'
        ? `${registro.correo} · acceso aceptado`
        : `${registro.correo} · invitación ${tiempoRelativo(registro.fecha_compartida) || 'enviada'}`;
    datos.appendChild(correo);

    const acciones = document.createElement('div');
    acciones.className = 'compartir-acciones';

    let permisoAnterior = registro.permiso;
    const select = crearSelectPermiso(registro.permiso, async (e) => {
        const nuevo = e.target.value;
        select.disabled = true;
        try {
            await api.patch(rutaDeRegistro(registro), { permiso: nuevo });
            registro.permiso = nuevo;
            permisoAnterior = nuevo;
            mostrarExito('Permiso actualizado.');
        } catch (error) {
            select.value = permisoAnterior;
            mostrarError(extraerError(error, 'No se pudo actualizar el permiso.'));
        } finally {
            select.disabled = false;
        }
    });
    acciones.appendChild(select);

    if (registro.estado !== 'aceptada') {
        acciones.appendChild(crearBotonIcono({
            icono: 'bi-arrow-clockwise',
            titulo: 'Reenviar invitación',
            clase: 'compartir-accion--reenviar',
            onClick: async (e) => {
                const boton = e.currentTarget;
                boton.disabled = true;
                try {
                    await api.post(`/compartir/invitaciones/${registro.id}/reenviar/`);
                    mostrarExito(`Invitación reenviada a ${registro.correo}.`);
                    await cargarLista(overlay, contexto);
                } catch (error) {
                    mostrarError(extraerError(error, 'No se pudo reenviar la invitación.'));
                    boton.disabled = false;
                }
            }
        }));
    }

    const esAcceso = registro.origen === 'comparticion';
    acciones.appendChild(crearBotonIcono({
        icono: 'bi-x-lg',
        titulo: esAcceso ? 'Quitar acceso' : 'Cancelar invitación',
        clase: 'compartir-accion--quitar',
        onClick: async () => {
            const confirmado = await confirmar({
                titulo: esAcceso ? 'Quitar acceso' : 'Cancelar invitación',
                mensaje: esAcceso
                    ? `¿Quitar el acceso de ${registro.correo}?`
                    : `¿Cancelar la invitación de ${registro.correo}?`,
                confirmarTexto: esAcceso ? 'Quitar' : 'Cancelar invitación',
                cancelarTexto: 'Volver',
                peligro: true
            });
            if (!confirmado) return;
            try {
                await api.delete(rutaDeRegistro(registro));
                mostrarExito(esAcceso ? 'Acceso eliminado.' : 'Invitación cancelada.');
                await cargarLista(overlay, contexto);
            } catch (error) {
                mostrarError(extraerError(error, 'No se pudo completar la operación.'));
            }
        }
    }));

    fila.append(avatar, datos, acciones);
    return fila;
}

async function cargarLista(overlay, contexto) {
    const lista = overlay.querySelector('.compartir-lista');
    const contador = overlay.querySelector('.compartir-contador');
    lista.innerHTML = '<p class="compartir-vacio compartir-vacio--cargando">Cargando…</p>';

    try {
        const registros = await api
            .get(`/compartir/lista/${contexto.tipo}/${contexto.objetoId}/`)
            .then(r => r.data);

        if (!Array.isArray(registros) || registros.length === 0) {
            contador.textContent = 'Nadie más tiene acceso';
            lista.innerHTML = `
                <div class="compartir-vacio">
                    <i class="bi bi-people"></i>
                    <p>Aún no has compartido este elemento.</p>
                    <span>Invita por correo a la persona con la que quieras colaborar.</span>
                </div>`;
            return;
        }

        const aceptados = registros.filter(r => r.estado === 'aceptada').length;
        const pendientes = registros.filter(r => r.estado === 'pendiente').length;
        const partes = [];
        if (aceptados) partes.push(`${aceptados} con acceso`);
        if (pendientes) partes.push(`${pendientes} pendiente${pendientes === 1 ? '' : 's'}`);
        contador.textContent = partes.join(' · ') || `${registros.length} invitaciones`;

        lista.innerHTML = '';
        registros.forEach(registro => {
            lista.appendChild(crearFila(registro, overlay, contexto));
        });
    } catch (error) {
        contador.textContent = '';
        lista.innerHTML = `
            <div class="compartir-vacio">
                <i class="bi bi-exclamation-triangle"></i>
                <p>No se pudo cargar la lista.</p>
                <span>${extraerError(error, 'Intenta de nuevo en unos segundos.')}</span>
            </div>`;
    }
}

export function abrirDialogoCompartir({ tipo, objetoId, titulo }) {
    if (dialogoAbierto) return;
    dialogoAbierto = true;

    const contexto = { tipo, objetoId };
    const esProyecto = tipo === 'proyecto';
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay abierto';
    overlay.innerHTML = `
        <div class="glass-card-strong modal-card compartir-card" role="dialog" aria-modal="true" aria-labelledby="compartir-titulo">
            <div class="compartir-cabecera">
                <div class="compartir-icono"><i class="bi bi-share-fill"></i></div>
                <div class="compartir-cabecera__texto">
                    <h3 class="modal-titulo" id="compartir-titulo">Compartir ${esProyecto ? 'proyecto' : 'tarea'}</h3>
                    <p class="compartir-subtitulo" id="compartir-objeto"></p>
                </div>
                <button type="button" class="compartir-cerrar" id="compartir-x" aria-label="Cerrar">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>

            <div class="compartir-ayuda">
                <i class="bi bi-envelope-paper"></i>
                <p>
                    <strong>Invitación por correo.</strong>
                    Enviaremos un enlace a la persona invitada. Tendrá acceso
                    cuando lo acepte, aunque todavía no tenga una cuenta en Orbit.
                </p>
            </div>

            <form class="compartir-form" id="compartir-form" novalidate>
                <div class="compartir-campo compartir-campo--correo">
                    <label class="etiqueta-form" for="compartir-correo">Correo de la persona</label>
                    <div class="campo-con-icono">
                        <i class="bi bi-envelope"></i>
                        <input class="input-dark" id="compartir-correo" type="email"
                               placeholder="correo@ejemplo.com" autocomplete="off">
                    </div>
                </div>
                <div class="compartir-campo compartir-campo--permiso">
                    <label class="etiqueta-form" for="compartir-permiso-nuevo">Permiso</label>
                    <select class="input-dark compartir-permiso-select" id="compartir-permiso-nuevo"></select>
                </div>
                <button class="btn-primary compartir-enviar" id="compartir-enviar" type="submit">
                    <i class="bi bi-send"></i> Invitar
                </button>
            </form>

            <div class="compartir-lista-cabecera">
                <span>Personas con acceso</span>
                <span class="compartir-contador"></span>
            </div>
            <div class="compartir-lista"></div>

            <div class="modal-acciones">
                <button class="btn-secondary" id="compartir-cerrar" type="button">Listo</button>
            </div>
        </div>
    `;

    overlay.querySelector('#compartir-objeto').textContent = titulo || '';

    const selectNuevo = overlay.querySelector('#compartir-permiso-nuevo');
    Object.keys(ETIQUETAS_PERMISO).forEach(permiso => {
        const opcion = document.createElement('option');
        opcion.value = permiso;
        opcion.textContent = ETIQUETAS_PERMISO[permiso];
        selectNuevo.appendChild(opcion);
    });
    selectNuevo.value = 'editar';

    function cerrar() {
        overlay.remove();
        dialogoAbierto = false;
        document.removeEventListener('keydown', manejarTeclas);
    }

    function manejarTeclas(e) {
        if (e.key === 'Escape') cerrar();
    }

    overlay.querySelector('#compartir-x').addEventListener('click', cerrar);
    overlay.querySelector('#compartir-cerrar').addEventListener('click', cerrar);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) cerrar();
    });
    document.addEventListener('keydown', manejarTeclas);

    const formulario = overlay.querySelector('#compartir-form');
    const inputCorreo = overlay.querySelector('#compartir-correo');
    const btnEnviar = overlay.querySelector('#compartir-enviar');

    formulario.addEventListener('submit', async (e) => {
        e.preventDefault();
        const correo = inputCorreo.value.trim();

        if (!validarCorreo(correo)) {
            mostrarError('Ingresa un correo válido.');
            inputCorreo.focus();
            return;
        }

        btnEnviar.disabled = true;
        btnEnviar.innerHTML = '<span class="loader-mini"></span> Enviando…';
        try {
            const { data } = await api.post('/compartir/', {
                correo,
                tipo_objeto: tipo,
                objeto_id: objetoId,
                permiso: selectNuevo.value
            });
            inputCorreo.value = '';

            if (data?.ya_tiene_acceso) {
                mostrarExito('Ese correo ya tenía acceso. Permiso actualizado.');
            } else if (data?.correo_enviado) {
                mostrarExito(`Invitación enviada a ${correo}.`);
            } else {
                mostrarExito('La invitación ya estaba pendiente. Actualizamos el permiso.');
            }

            await cargarLista(overlay, contexto);
        } catch (error) {
            mostrarError(extraerError(error));
        } finally {
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = '<i class="bi bi-send"></i> Invitar';
            inputCorreo.focus();
        }
    });

    document.body.appendChild(overlay);
    cargarLista(overlay, contexto);
    inputCorreo.focus();
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
