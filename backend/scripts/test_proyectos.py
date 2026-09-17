"""
Prueba de humo específica del módulo de proyectos (RF-PRO-01 a RF-PRO-06).
Ejecutar con el servidor levantado en http://127.0.0.1:8000
"""
import os
import sys
import uuid
import requests

BASE = os.environ.get('API_BASE_URL', 'http://127.0.0.1:8000')
CAPTCHA = 'token-de-prueba'
fallos = []


def verificar(nombre, condicion, detalle=''):
    estado = 'OK ' if condicion else 'FALLO'
    print(f"[{estado}] {nombre}" + (f" -> {detalle}" if detalle else ''))
    if not condicion:
        fallos.append(nombre)


def main():
    sufijo = uuid.uuid4().hex[:8]
    correo = f"proy_{sufijo}@orbit.test"
    contrasena = "Proyecto123"

    # Registrar y loguear un usuario normal
    r = requests.post(f"{BASE}/api/v1/usuarios/registro/", json={
        'nombre_completo': 'Probador de Proyectos',
        'correo': correo, 'contrasena': contrasena, 'captcha_token': CAPTCHA,
    }, timeout=10)
    verificar("Registro usuario", r.status_code == 201, str(r.status_code))
    token = r.json()['tokens']['access']
    h = {'Authorization': f'Bearer {token}'}

    # RF-PRO-01: crear proyecto
    r = requests.post(f"{BASE}/api/v1/proyectos/", headers=h, json={
        'nombre': 'Sitio Web Corporativo',
        'descripcion': 'Rediseño del sitio principal',
        'color': '#00E5FF',
        'estado': 'activo',
    }, timeout=10)
    verificar("Crear proyecto", r.status_code == 201, str(r.status_code))
    pid = r.json()['id']
    verificar("Crear proyecto retorna id", bool(pid))

    # RF-PRO-02: listar proyectos propios
    r = requests.get(f"{BASE}/api/v1/proyectos/", headers=h, timeout=10)
    verificar("Listar proyectos propios",
              r.status_code == 200 and any(p['id'] == pid for p in r.json()),
              str(r.status_code))

    # Vincular una tarea a un proyecto
    t = requests.post(f"{BASE}/api/v1/tareas/", headers=h, json={
        'titulo': 'Diseñar home', 'proyecto': pid,
    }, timeout=10)
    verificar("Crear tarea vinculada", t.status_code == 201, str(t.status_code))

    # RF-PRO-03: ver detalle con tareas y métricas
    r = requests.get(f"{BASE}/api/v1/proyectos/{pid}/", headers=h, timeout=10)
    datos = r.json()
    verificar("Detalle proyecto con tareas",
              r.status_code == 200 and len(datos.get('tareas', [])) == 1 and
              datos.get('tareas_totales') == 1,
              f"tareas={len(datos.get('tareas', []))}, total={datos.get('tareas_totales')}")

    # RF-PRO-04: editar proyecto
    r = requests.patch(f"{BASE}/api/v1/proyectos/{pid}/", headers=h, json={
        'nombre': 'Sitio Web Corporativo v2'
    }, timeout=10)
    verificar("Editar proyecto", r.status_code == 200 and
              r.json().get('nombre') == 'Sitio Web Corporativo v2',
              str(r.status_code))

    # Archivar / restaurar
    r = requests.patch(f"{BASE}/api/v1/proyectos/{pid}/archivar/", headers=h, timeout=10)
    verificar("Archivar proyecto", r.status_code == 200 and
              r.json().get('estado') == 'archivado')
    r = requests.patch(f"{BASE}/api/v1/proyectos/{pid}/archivar/", headers=h, timeout=10)
    verificar("Restaurar proyecto", r.status_code == 200 and
              r.json().get('estado') == 'activo')

    # RF-PRO-06: admin ve todos
    admin = requests.post(f"{BASE}/api/v1/usuarios/login/", json={
        'correo': 'admin@orbit.local', 'contrasena': 'Admin1234',
        'captcha_token': CAPTCHA,
    }, timeout=10)
    if admin.status_code == 200:
        ah = {'Authorization': f"Bearer {admin.json()['tokens']['access']}"}
        r = requests.get(f"{BASE}/api/v1/proyectos/admin/todos/", headers=ah, timeout=10)
        verificar("Admin ve todos los proyectos",
                  r.status_code == 200 and any(p.get('id') == pid for p in r.json()),
                  str(r.status_code))
        if r.status_code == 200:
            encontrado = next((p for p in r.json() if p.get('id') == pid), None)
            verificar("Proyecto incluye propietario",
                      encontrado and 'propietario' in encontrado)
    else:
        verificar("Login admin", False, str(admin.status_code))

    # RF-PRO-06 bloqueado para usuario normal
    r = requests.get(f"{BASE}/api/v1/proyectos/admin/todos/", headers=h, timeout=10)
    verificar("Admin/todos bloqueado para usuario", r.status_code == 403, str(r.status_code))

    # RF-PRO-05: eliminar proyecto (la tarea debe quedar sin proyecto)
    r = requests.delete(f"{BASE}/api/v1/proyectos/{pid}/", headers=h, timeout=10)
    verificar("Eliminar proyecto", r.status_code == 200, str(r.status_code))
    t = requests.get(f"{BASE}/api/v1/tareas/", headers=h, timeout=10)
    tarea = next((x for x in t.json() if x.get('proyecto') == '' and x.get('origen_nodo') == ''), None)
    verificar("Tarea desvinculada tras eliminar proyecto",
              t.status_code == 200 and tarea is not None)

    print()
    if fallos:
        print(f"RESULTADO: {len(fallos)} fallo(s): {fallos}")
        sys.exit(1)
    print("RESULTADO: todas las pruebas de proyectos pasaron")


if __name__ == '__main__':
    main()
