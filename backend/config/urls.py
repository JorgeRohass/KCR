from django.db import connection
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from catalogo.views import cerrar_sesion, iniciar_sesion, usuario_actual


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
]
