from django.db import connection
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from catalogo.views import (
    aceptar_invitacion_usuario,
    cerrar_sesion,
    crear_invitacion_usuario,
    iniciar_sesion,
    usuario_actual,
)


@api_view(['GET'])
def health(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    return Response({'status': 'ok', 'database': 'connected'})


urlpatterns = [
    path('api/health/', health, name='health'),
    path('api/auth/login/', iniciar_sesion, name='login'),
    path('api/auth/logout/', cerrar_sesion, name='logout'),
    path('api/auth/me/', usuario_actual, name='current-user'),
    path(
        'api/auth/invitations/accept/',
        aceptar_invitacion_usuario,
        name='accept-invitation',
    ),
    path(
        'api/invitations/',
        crear_invitacion_usuario,
        name='create-invitation',
    ),
]
