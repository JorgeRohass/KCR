from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
)
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from catalogo.models import Usuario
from catalogo.serializers import (
    AceptarInvitacionSerializer,
    CrearInvitacionSerializer,
    LoginSerializer,
)
from catalogo.services import (
    CorreoYaRegistrado,
    InvitacionNoValida,
    aceptar_invitacion,
    crear_invitacion,
)


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes([AllowAny])
def iniciar_sesion(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email'].strip().lower()
    usuario = authenticate(
        request=request._request,
        email=email,
        password=serializer.validated_data['password'],
    )
    if usuario is None:
        return Response(
            {'detail': 'Correo o contraseña incorrectos.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    login(request._request, usuario)
    return Response(
        {
            'detail': 'Inicio de sesión exitoso.',
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
def cerrar_sesion(request):
    logout(request._request)
    return Response(
        {'detail': 'Cierre de sesión exitoso.'},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usuario_actual(request):
    usuario = request.user
    return Response(
        {
            'nombre_completo': f'{usuario.nombre} {usuario.apellidos}'.strip(),
            'rol': usuario.rol,
            'rol_nombre': usuario.get_rol_display(),
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes([IsAuthenticated])
def crear_invitacion_usuario(request):
    creador = request.user
    if creador.rol != Usuario.Rol.ADMIN:
        return Response(
            {'detail': 'Solo un administrador puede crear invitaciones.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = CrearInvitacionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    datos = serializer.validated_data
    if (
        datos['rol'] == Usuario.Rol.ADMIN
        and not creador.puede_crear_administradores
    ):
        return Response(
            {
                'detail': (
                    'Solo el administrador principal puede invitar '
                    'a otros administradores.'
                ),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        usuario, invitacion, token = crear_invitacion(
            email=datos['email'],
            nombre=datos['nombre'],
            apellidos=datos['apellidos'],
            rol=datos['rol'],
            creado_por=creador,
        )
    except CorreoYaRegistrado:
        return Response(
            {'email': ['Ya existe una cuenta con este correo electrónico.']},
            status=status.HTTP_400_BAD_REQUEST,
        )

    url = (
        f'{settings.FRONTEND_BASE_URL}/?'
        f'{urlencode({"invitation_token": token})}'
    )
    response = Response(
        {
            'detail': 'Invitación creada.',
            'invitacion_url': url,
            'expira_en': invitacion.expira_en,
            'usuario': {
                'email': usuario.email,
                'nombre': usuario.nombre,
                'apellidos': usuario.apellidos,
                'rol': usuario.rol,
            },
        },
        status=status.HTTP_201_CREATED,
    )
    response['Cache-Control'] = 'no-store'
    return response


@api_view(['POST'])
@parser_classes([JSONParser])
@permission_classes([AllowAny])
def aceptar_invitacion_usuario(request):
    serializer = AceptarInvitacionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        aceptar_invitacion(
            token=serializer.validated_data['token'],
            password=serializer.validated_data['password'],
        )
    except InvitacionNoValida:
        return Response(
            {'detail': 'La invitación no es válida o ha expirado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ValidationError as error:
        return Response(
            {'password': error.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {'detail': 'Cuenta activada. Ya puedes iniciar sesión.'},
        status=status.HTTP_200_OK,
    )
