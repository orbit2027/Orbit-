/**
 * Sincronización ligera por polling para vistas compartidas.
 * Cada `intervalo` ms consulta los datos remotos; si la firma cambió respecto
 * a la última firma aplicada, llama a `alCambiar(resultado)` para re-renderizar.
 *
 * Se puede pausar en plena interacción (arrastre, edición) con pausarSincronizacion().
 * Contrato de `consultar()`: devuelve `{ firma, datos }` o `null` en error.
 * Contrato de `alCambiar(resultado)`: aplica los cambios y devuelve `true`;
 * si devuelve `false`, no se fija la firma y se reintentará en el siguiente ciclo.
 */
let temporizador = null;
let pausado = false;
let ocupado = false;

export function iniciarSincronizacion({ consultar, alCambiar, intervalo = 5000 }) {
    detenerSincronizacion();
    let ultimaFirma;

    temporizador = setInterval(async () => {
        if (pausado || ocupado) return;
        ocupado = true;
        try {
            const resultado = await consultar();
            if (!resultado) return;
            if (resultado.firma !== ultimaFirma) {
                const aplicado = await alCambiar(resultado);
                if (aplicado !== false) ultimaFirma = resultado.firma;
            }
        } catch (_error) {
            // Silencioso: el backend puede estar reiniciándose o sin red.
        } finally {
            ocupado = false;
        }
    }, intervalo);
}

export function pausarSincronizacion() {
    pausado = true;
}

export function reanudarSincronizacion() {
    pausado = false;
}

export function detenerSincronizacion() {
    if (temporizador !== null) {
        clearInterval(temporizador);
        temporizador = null;
    }
}