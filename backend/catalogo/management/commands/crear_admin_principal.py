from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction

from catalogo.models import Usuario


class Command(BaseCommand):
    help = 'Inicializa el administrador principal en una base sin usuarios.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--nombre', required=True)
        parser.add_argument('--apellidos', required=True)
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma explícitamente la inicialización del administrador principal.',
        )

    def handle(self, *args, **options):
        if not options['confirmar']:
            raise CommandError(
                'Confirma la inicialización agregando la opción --confirmar.'
            )

        email = options['email'].strip().lower()
        try:
            validate_email(email)
        except ValidationError as error:
            raise CommandError('Ingresa un correo electrónico válido.') from error

        nombre = options['nombre'].strip()
        apellidos = options['apellidos'].strip()
        if not nombre or not apellidos:
            raise CommandError('El nombre y los apellidos son obligatorios.')

        password = getpass('Contraseña del administrador principal: ')
        password_confirmation = getpass('Confirma la contraseña: ')
        if password != password_confirmation:
            raise CommandError('Las contraseñas no coinciden.')
        if len(password) < 8:
            raise CommandError('La contraseña debe tener al menos 8 caracteres.')

        usuario_para_validacion = Usuario(
            email=email,
            nombre=nombre,
            apellidos=apellidos,
            rol=Usuario.Rol.ADMIN,
        )
        try:
            validate_password(password, user=usuario_para_validacion)
        except ValidationError as error:
            raise CommandError('Contraseña no válida: ' + ' '.join(error.messages)) from error

        try:
            with transaction.atomic():
                if Usuario.objects.exists():
                    raise CommandError(
                        'La tabla de usuarios no está vacía. '
                        'El administrador principal solo puede inicializarse '
                        'antes de crear otras cuentas.'
                    )
                usuario = Usuario.objects.create_user(
                    email=email,
                    password=password,
                    nombre=nombre,
                    apellidos=apellidos,
                    rol=Usuario.Rol.ADMIN,
                    puede_crear_administradores=True,
                    is_active=True,
                    is_staff=False,
                    is_superuser=False,
                )
        except IntegrityError as error:
            raise CommandError(
                'No se pudo crear el administrador principal; comprueba si otra '
                'inicialización ya creó una cuenta.'
            ) from error

        self.stdout.write(
            self.style.SUCCESS(
                f'Administrador principal {usuario.email} creado. '
                'No tiene privilegios de superusuario de Django.'
            )
        )
