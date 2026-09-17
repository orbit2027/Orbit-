"""
Vistas API para el módulo de usuarios.
Implementa registro, login, perfil, edición, eliminación y logout.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q

from .modelo import Usuario
from .serializador import (
    RegistroUsuarioSerializador,
    LoginUsuarioSerializador,
    PerfilUsuarioSerializador,
    EditarUsuarioSerializador,
    EliminarCuentaSerializador
)
from apps.tareas.modelo import Tarea
from apps.proyectos.modelo import Proyecto
from apps.mapa_mental.modelo import NodoMapa, ConexionNodo
from apps.comparticion.modelo import Comparticion

@api_view(['POST'])
@permission_classes([AllowAny])
def registrar_usuario(request):
    """
    RF-USU-01: Registro de nuevo usuario con CAPTCHA.
    Retorna tokens JWT para auto-login después del registro.
    """
    serializador = RegistroUsuarioSerializador(data=request.data)
    if serializador.is_valid():
        usuario = serializador.save()
        # Auto-login: generar tokens después del registro
        refresh = RefreshToken.for_user(usuario)
        return Response({
            'mensaje': 'Usuario registrado exitosamente',
            'usuario': PerfilUsuarioSerializador(usuario).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def iniciar_sesion(request):
    """
    RF-USU-02: Inicio de sesión con CAPTCHA.
    Error genérico si las credenciales fallan.
    """
    serializador = LoginUsuarioSerializador(data=request.data)
    if not serializador.is_valid():
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_400_BAD_REQUEST
        )

    correo = serializador.validated_data['correo'].lower().strip()
    contrasena = serializador.validated_data['contrasena']

    usuario = Usuario.objects.filter(correo=correo, activo=True).first()

    # Error genérico para no revelar si el correo existe
    if not usuario or not usuario.verificar_contrasena(contrasena):
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    refresh = RefreshToken.for_user(usuario)
    return Response({
        'usuario': PerfilUsuarioSerializador(usuario).data,
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ver_perfil(request):
    """Visualización del perfil del usuario autenticado."""
    serializador = PerfilUsuarioSerializador(request.user)
    return Response(serializador.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def editar_perfil(request):
    """
    Edición de perfil.
    Permite modificar nombre, correo y contraseña.
    Para cambiar contraseña se requiere confirmar la actual.
    """
    serializador = EditarUsuarioSerializador(
        data=request.data,
        context={'usuario_actual': request.user}
    )
    if not serializador.is_valid():
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    usuario = request.user
    datos = serializador.validated_data

    # Actualizar campos si se proporcionaron
    if 'nombre_completo' in datos:
        usuario.nombre_completo = datos['nombre_completo']
    if 'correo' in datos:
        usuario.correo = datos['correo']

    # Cambiar contraseña solo si se proporcionan ambos campos
    if 'contrasena_nueva' in datos and 'contrasena_actual' in datos:
        if not usuario.verificar_contrasena(datos['contrasena_actual']):
            return Response(
                {'error': 'La contraseña actual es incorrecta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        usuario.set_contrasena(datos['contrasena_nueva'])

    usuario.save()
    return Response({
        'mensaje': 'Perfil actualizado exitosamente',
        'usuario': PerfilUsuarioSerializador(usuario).data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_cuenta(request):
    """
    Eliminación permanente de cuenta con cascada.
    Elimina todas las tareas, nodos y conexiones del usuario.
    """
    serializador = EliminarCuentaSerializador(
        data=request.data,
        context={'usuario_actual': request.user}
    )
    if not serializador.is_valid():
        return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)

    usuario = request.user

    # Borrado explícito en orden de dependencias: evita fallos de integridad
    # del FastDelete de Django con foreign keys "INITIALLY DEFERRED" de SQLite.
    Comparticion.objects.filter(
        Q(propietario=usuario) | Q(compartido_con=usuario)
    ).delete()
    Tarea.objects.filter(usuario=usuario).delete()
    Proyecto.objects.filter(usuario=usuario).delete()
    NodoMapa.objects.filter(usuario=usuario).delete()
    ConexionNodo.objects.filter(usuario=usuario).delete()
    usuario.delete()

    return Response(
        {'mensaje': 'Cuenta eliminada permanentemente'},
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cerrar_sesion(request):
    """
    Cierre de sesión.
    El JWT se elimina del lado del cliente (localStorage).
    Esta vista solo confirma el cierre.
    """
    return Response(
        {'mensaje': 'Sesión cerrada exitosamente'},
        status=status.HTTP_200_OK
    )