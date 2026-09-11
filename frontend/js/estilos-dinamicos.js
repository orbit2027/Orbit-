function aplicarEstilosDinamicos(elemento) {
    elemento.querySelectorAll('[data-color]').forEach(nodo => {
        nodo.style.backgroundColor = nodo.dataset.color;
    });
    elemento.querySelectorAll('[data-text-color]').forEach(nodo => {
        nodo.style.color = nodo.dataset.textColor;
    });
    elemento.querySelectorAll('[data-progress]').forEach(nodo => {
        nodo.style.width = `${nodo.dataset.progress}%`;
    });
}

aplicarEstilosDinamicos(document);
new MutationObserver(mutations => {
    mutations.forEach(mutation => mutation.addedNodes.forEach(nodo => {
        if (nodo.nodeType === Node.ELEMENT_NODE) aplicarEstilosDinamicos(nodo);
    }));
}).observe(document.body, { childList: true, subtree: true });
