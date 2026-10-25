import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction

from catalogo.models import Usuario


USUARIOS_PRUEBA = (
    (
        Usuario.Rol.ADMIN,
        'Admin',
        'Prueba',
        'TEST_ADMIN_EMAIL',
        'TEST_ADMIN_PASSWORD',
    ),
    (
        Usuario.Rol.OPERADOR,
        'Operador',
        'Prueba',
        'TEST_OPERADOR_EMAIL',
        'TEST_OPERADOR_PASSWORD',
    ),
    (
        Usuario.Rol.CLIENTE,
        'Cliente',
        'Prueba',
        'TEST_CLIENTE_EMAIL',
        'TEST_CLIENTE_PASSWORD',
    ),
)


class Command(BaseCommand):
    help = 'Crea, una sola vez, las cuentas base de prueba para cada rol.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enable-test-users',
            action='store_true',
            help='Confirma explícitamente la creación de cuentas de prueba.',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG or not settings.ALLOW_TEST_USERS:
            raise CommandError(
                'Las cuentas de prueba requieren DEBUG=True y ALLOW_TEST_USERS=True.'
            )
        if not options['enable_test_users']:
            raise CommandError(
                'La creación está desactivada. Repite el comando con '
                '--enable-test-users solo en un entorno local de pruebas.'
            )

        cuentas = []
        for rol, nombre, apellidos, email_variable, password_variable in USUARIOS_PRUEBA:
            email = os.getenv(email_variable, '').strip().lower()
            password = os.getenv(password_variable, '')
            if not email or not password:
                raise CommandError(
                    f'Debes configurar {email_variable} y {password_variable} '
                    'en el entorno local.'
                )
            try:
                validate_email(email)
            except ValidationError as error:
                raise CommandError(f'{email_variable} no contiene un correo válido.') from error
            if len(password) < 16:
                raise CommandError(
                    f'{password_variable} debe tener al menos 16 caracteres.'
                )
            cuentas.append((rol, nombre, apellidos, email, password))

        emails = [cuenta[3] for cuenta in cuentas]
        if len(set(emails)) != len(emails):
            raise CommandError('Cada usuario de prueba debe tener un correo distinto.')

        with transaction.atomic():
            for rol, nombre, apellidos, email, password in cuentas:
                usuario_existente = Usuario.objects.filter(email=email).first()
                if usuario_existente:
                    if usuario_existente.rol != rol:
                        raise CommandError(
                            f'{email} ya existe con otro rol; no se modificó.'
                        )
                    self.stdout.write(
                        f'Ya existe {email} con rol {rol}; no se modificó.'
                    )
                    continue

                Usuario.objects.create_user(
                    email=email,
                    password=password,
                    nombre=nombre,
                    apellidos=apellidos,
                    rol=rol,
                    is_active=True,
                )
                self.stdout.write(self.style.SUCCESS(f'Creado {email} con rol {rol}.'))
