from django.contrib.auth import authenticate, login
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
)
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from catalogo.serializers import LoginSerializer


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
