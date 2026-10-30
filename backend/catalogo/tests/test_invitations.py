import hashlib
from urllib.parse import parse_qs, urlparse

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from catalogo.models import Invitacion, Usuario


class InvitacionTests(APITestCase):
    create_url = '/api/invitations/'
    accept_url = '/api/auth/invitations/accept/'

    def setUp(self):
        self.administrador_principal = Usuario.objects.create_user(
            email='principal@example.com',
            password='Contrasena-segura-123!',
            nombre='Admin',
            apellidos='Principal',
            rol=Usuario.Rol.ADMIN,
            puede_crear_administradores=True,
            is_active=True,
        )
        self.administrador = Usuario.objects.create_user(
            email='admin@example.com',
            password='Contrasena-segura-123!',
            nombre='Admin',
            apellidos='Regular',
            rol=Usuario.Rol.ADMIN,
            is_active=True,
        )
        self.operador = Usuario.objects.create_user(
            email='operador@example.com',
            password='Contrasena-segura-123!',
            nombre='Operador',
            apellidos='Prueba',
            rol=Usuario.Rol.OPERADOR,
            is_active=True,
        )
        self.datos_invitacion = {
            'email': 'invitado@example.com',
            'nombre': 'Persona',
            'apellidos': 'Invitada',
            'rol': Usuario.Rol.CLIENTE,
        }

    def test_administrador_crea_invitacion_y_recibe_enlace(self):
        self.client.force_authenticate(self.administrador)

        response = self.client.post(
            self.create_url,
            self.datos_invitacion,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        usuario = Usuario.objects.get(email='invitado@example.com')
        invitacion = Invitacion.objects.get(usuario=usuario)
        token = parse_qs(
            urlparse(response.data['invitacion_url']).query
        )['invitation_token'][0]
        self.assertEqual(
            response.data['invitacion_url'].split('?')[0],
            'http://localhost:5173/',
        )
        self.assertEqual(
            invitacion.token_hash,
            hashlib.sha256(token.encode()).hexdigest(),
        )
        self.assertEqual(invitacion.creado_por, self.administrador)
        self.assertFalse(usuario.is_active)
        self.assertFalse(usuario.has_usable_password())
        self.assertNotIn('token', response.data)
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_solo_administrador_principal_puede_invitar_administradores(self):
        self.client.force_authenticate(self.administrador)
        datos = {**self.datos_invitacion, 'rol': Usuario.Rol.ADMIN}

        response = self.client.post(self.create_url, datos, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Usuario.objects.filter(email=self.datos_invitacion['email']).exists()
        )

        self.client.force_authenticate(self.administrador_principal)
        response = self.client.post(self.create_url, datos, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Usuario.objects.get(email=self.datos_invitacion['email']).rol,
            Usuario.Rol.ADMIN,
        )

    def test_usuario_no_administrador_no_puede_invitar(self):
        self.client.force_authenticate(self.operador)

        response = self.client.post(
            self.create_url,
            self.datos_invitacion,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_crear_invitacion_requiere_autenticacion(self):
        response = self.client.post(
            self.create_url,
            self.datos_invitacion,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_permite_invitar_un_correo_existente(self):
        self.client.force_authenticate(self.administrador)
        datos = {**self.datos_invitacion, 'email': self.operador.email}

        response = self.client.post(self.create_url, datos, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_aceptar_invitacion_activa_usuario_y_token_no_se_reutiliza(self):
        self.client.force_authenticate(self.administrador)
        crear_response = self.client.post(
            self.create_url,
            self.datos_invitacion,
            format='json',
        )
        token = parse_qs(
            urlparse(crear_response.data['invitacion_url']).query
        )['invitation_token'][0]
        datos = {
            'token': token,
            'password': 'Invitacion-segura-2026!',
            'confirmar_password': 'Invitacion-segura-2026!',
        }
        self.client.force_authenticate(user=None)

        response = self.client.post(self.accept_url, datos, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usuario = Usuario.objects.get(email=self.datos_invitacion['email'])
        self.assertTrue(usuario.is_active)
        self.assertTrue(usuario.check_password(datos['password']))
        self.assertIsNotNone(Invitacion.objects.get(usuario=usuario).usado_en)

        response = self.client.post(self.accept_url, datos, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'La invitación no es válida o ha expirado.',
        )

    def test_invitacion_expirada_no_puede_aceptarse(self):
        self.client.force_authenticate(self.administrador)
        crear_response = self.client.post(
            self.create_url,
            self.datos_invitacion,
            format='json',
        )
        token = parse_qs(
            urlparse(crear_response.data['invitacion_url']).query
        )['invitation_token'][0]
        invitacion = Invitacion.objects.get(
            usuario__email=self.datos_invitacion['email'],
        )
        invitacion.expira_en = timezone.now()
        invitacion.save(update_fields=['expira_en'])
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.accept_url,
            {
                'token': token,
                'password': 'Invitacion-segura-2026!',
                'confirmar_password': 'Invitacion-segura-2026!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(invitacion.usuario.is_active)

    def test_aceptacion_rechaza_contrasena_debil_o_distinta(self):
        self.client.force_authenticate(self.administrador)
        crear_response = self.client.post(
            self.create_url,
            self.datos_invitacion,
            format='json',
        )
        token = parse_qs(
            urlparse(crear_response.data['invitacion_url']).query
        )['invitation_token'][0]
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.accept_url,
            {
                'token': token,
                'password': '12345678',
                'confirmar_password': '12345678',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

        response = self.client.post(
            self.accept_url,
            {
                'token': token,
                'password': 'Invitacion-segura-2026!',
                'confirmar_password': 'otra-contrasena',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirmar_password', response.data)
