import api from './api.js';
import { obtenerUsuario } from './autenticacion.js';

let configuracionPublicaEnCurso = null;

export function obtenerConfiguracionPublica() {
    if (!configuracionPublicaEnCurso) {
        configuracionPublicaEnCurso = api.get('/administracion/configuracion/publica/')
            .then(respuesta => respuesta.data)
            .catch((error) => {
                configuracionPublicaEnCurso = null;
                throw error;
            });
    }
    return configuracionPublicaEnCurso;
}

export function refrescarAvisoGlobal() {
    configuracionPublicaEnCurso = null;
    document.getElementById('aviso-global-orbit')?.remove();
    inicializarAvisoGlobal();
}

export function inicializarAvisoGlobal() {
    if (document.getElementById('aviso-global-orbit')) return;

    obtenerConfiguracionPublica()
        .then((configuracion) => {
            const usuario = obtenerUsuario();
            const avisos = [];
            if (
                configuracion.mantenimiento_activo &&
                usuario?.rol !== 'administrador'
            ) {
                avisos.push(configuracion.mensaje_mantenimiento);
            }
            if (configuracion.aviso_global) {
                avisos.push(configuracion.aviso_global);
            }
            if (!avisos.length) return;

            const aviso = document.createElement('div');
            aviso.id = 'aviso-global-orbit';
            aviso.className = 'aviso-global-orbit';
            aviso.setAttribute('role', 'status');
            aviso.setAttribute('aria-live', 'polite');
            aviso.textContent = avisos.join(' — ');
            document.body.prepend(aviso);
        })
        .catch((error) => {
            console.error('No se pudo cargar el aviso de Orbit:', error);
        });
}
