"""Inicia el backend Django y el frontend estático para desarrollo local."""
import subprocess
import sys
import time
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BACKEND_DIR.parent / 'frontend'


def detener(proceso):
    if proceso.poll() is not None:
        return
    proceso.terminate()
    try:
        proceso.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proceso.kill()
        proceso.wait()


def main():
    backend = None
    frontend = None
    try:
        backend = subprocess.Popen(
            [
                sys.executable,
                str(BACKEND_DIR / 'manage.py'),
                'runserver',
                'localhost:8000',
                '--noreload',
            ],
            cwd=BACKEND_DIR,
        )
        frontend = subprocess.Popen(
            [
                sys.executable,
                '-m',
                'http.server',
                '5500',
                '--bind',
                'localhost',
                '--directory',
                str(FRONTEND_DIR),
            ],
            cwd=BACKEND_DIR,
        )
        print('Frontend: http://localhost:5500', flush=True)
        print('Backend:  http://localhost:8000/api/v1/', flush=True)
        print('Presiona Ctrl+C para detener ambos servidores.', flush=True)

        while True:
            if backend.poll() is not None:
                raise RuntimeError(
                    f'El backend terminó con código {backend.returncode}.'
                )
            if frontend.poll() is not None:
                raise RuntimeError(
                    f'El frontend terminó con código {frontend.returncode}.'
                )
            time.sleep(0.25)
    except KeyboardInterrupt:
        print('\nDeteniendo servidores...', flush=True)
    finally:
        if frontend is not None:
            detener(frontend)
        if backend is not None:
            detener(backend)


if __name__ == '__main__':
    main()
