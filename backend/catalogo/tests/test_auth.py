from rest_framework import status
from rest_framework.test import APITestCase

from catalogo.models import Usuario

#Pruebas Logins
class LoginTests(APITestCase):
    url = '/api/auth/login/'

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='usuario@example.com',
            password='Contrasena-segura-123!',
            nombre='Usuario',
            apellidos='De Prueba',
            rol=Usuario.Rol.CLIENTE,
            is_active=True,
        )
    # test inicio de sesión
    def test_login_crea_sesion(self):
        response = self.client.post(
            self.url,
            {
                'email': ' USUARIO@example.com ',
                'password': 'Contrasena-segura-123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'detail': 'Inicio de sesión exitoso.',
            },
        )
        self.assertEqual(
            self.client.session['_auth_user_id'],
            str(self.usuario.pk),
        )
        self.assertNotIn('password', response.data)
        self.assertIn('csrftoken', response.cookies)

    def test_credenciales_incorrectas_devuelven_error_generico(self):
        response = self.client.post(
            self.url,
            {
                'email': self.usuario.email,
                'password': 'incorrecta',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            response.data,
            {'detail': 'Correo o contraseña incorrectos.'},
        )

    def test_usuario_inactivo_no_puede_iniciar_sesion(self):
        self.usuario.is_active = False
        self.usuario.save(update_fields=['is_active'])

        response = self.client.post(
            self.url,
            {
                'email': self.usuario.email,
                'password': 'Contrasena-segura-123!',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_datos_invalidos_devuelven_error_de_validacion(self):
        response = self.client.post(
            self.url,
            {'email': 'correo-invalido', 'password': 'cualquiera'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
