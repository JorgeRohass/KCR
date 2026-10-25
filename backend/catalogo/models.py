from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio.')

        email = self.normalize_email(email).strip().lower()
        usuario = self.model(email=email, **extra_fields)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('rol', Usuario.Rol.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('rol') != Usuario.Rol.ADMIN:
            raise ValueError('El superusuario debe tener rol admin.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Rol(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        OPERADOR = 'operador', 'Operador'
        CLIENTE = 'cliente', 'Cliente'

    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150)
    rol = models.CharField(max_length=20, choices=Rol.choices)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellidos']

    class Meta:
        db_table = 'usuario'
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return self.email


class Invitacion(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='invitacion',
    )
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='invitaciones_creadas',
    )
    token_hash = models.CharField(max_length=64, unique=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'invitacion'
        verbose_name = 'invitación'
        verbose_name_plural = 'invitaciones'

    def __str__(self):
        return f'Invitación para {self.usuario.email}'


class Catalogo(models.Model):
    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='catalogos_cliente',
    )
    operadores = models.ManyToManyField(
        Usuario,
        through='CatalogoOperador',
        related_name='catalogos_asignados',
    )
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='catalogos_creados',
    )
    cliente_puede_editar = models.BooleanField(default=False)
    operador_puede_editar = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    actualizacion_habilitada = models.BooleanField(default=False)

    class Meta:
        db_table = 'catalogo'
        verbose_name = 'catálogo'
        verbose_name_plural = 'catálogos'

    def __str__(self):
        return f'Catálogo {self.pk} (cliente: {self.cliente})'


class CatalogoOperador(models.Model):
    catalogo = models.ForeignKey(
        Catalogo,
        on_delete=models.CASCADE,
        related_name='asignaciones_operador',
    )
    operador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='asignaciones_operador',
    )

    class Meta:
        db_table = 'catalogo_operador'
        constraints = [
            models.UniqueConstraint(
                fields=('catalogo', 'operador'),
                name='catalogo_operador_unico',
            ),
        ]

    def __str__(self):
        return f'{self.operador} - {self.catalogo}'


class Producto(models.Model):
    catalogo = models.ForeignKey(
        Catalogo,
        on_delete=models.CASCADE,
        related_name='productos',
    )
    foto = models.URLField(blank=True)
    titulo = models.CharField(max_length=200)
    origen = models.CharField(max_length=150, blank=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.TextField(blank=True)
    url = models.URLField(blank=True)
    codigo_sku = models.CharField(max_length=100)
    capacidad = models.CharField(max_length=100, blank=True)
    organizacion = models.CharField(max_length=150, blank=True)
    flag_visibilidad = models.BooleanField(default=True)

    class Meta:
        db_table = 'producto'
        verbose_name = 'producto'
        verbose_name_plural = 'productos'

    def __str__(self):
        return self.titulo


class VersionPreviaCatalogo(models.Model):
    catalogo = models.ForeignKey(
        Catalogo,
        on_delete=models.CASCADE,
        related_name='versiones_previas',
    )
    editor = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='versiones_editadas',
    )
    version = models.PositiveIntegerField()
    cambios = models.TextField()

    class Meta:
        db_table = 'version_previa_catalogo'
        verbose_name = 'versión previa de catálogo'
        verbose_name_plural = 'versiones previas de catálogo'
        constraints = [
            models.UniqueConstraint(
                fields=('catalogo', 'version'),
                name='catalogo_version_unica',
            ),
        ]

    def __str__(self):
        return f'{self.catalogo} - versión {self.version}'
