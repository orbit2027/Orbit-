"""
Copia el frontend dentro de `backend/` para el despliegue en Vercel.

Vercel empaqueta la función Python tomando como raíz la carpeta que contiene
`manage.py` (backend/). Por eso los archivos de `frontend/` no llegan a la
función salvo que estén dentro de `backend/`. Este script se ejecuta en el
build de Vercel, antes de empaquetar la función.
"""
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ORIGEN = RAIZ / "frontend"
DESTINO = RAIZ / "backend" / "frontend"


def main():
    if not ORIGEN.is_dir():
        sys.exit(f"No se encontró el frontend en {ORIGEN}")

    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    shutil.copytree(ORIGEN, DESTINO)

    archivos = sum(1 for _ in DESTINO.rglob("*") if _.is_file())
    print(f"Frontend copiado a {DESTINO} ({archivos} archivos)")


if __name__ == "__main__":
    main()
