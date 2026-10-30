import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from catalogo.models import (
    Catalogo,
    Invitacion,
    Producto,
    ProductoVersion,
    Usuario,
    VersionCatalogo,
)


class InvitacionNoValida(Exception):
    pass


class CorreoYaRegistrado(Exception):
    pass


@transaction.atomic
def crear_invitacion(
    *,
    email: str,
    nombre: str,
    apellidos: str,
    rol: str,
    creado_por: Usuario,
) -> tuple[Usuario, Invitacion, str]:
    email = email.strip().lower()
    if Usuario.objects.filter(email=email).exists():
        raise CorreoYaRegistrado

    token = secrets.token_urlsafe(32)
    try:
        with transaction.atomic():
            usuario = Usuario.objects.create_user(
                email=email,
                password=None,
                nombre=nombre.strip(),
                apellidos=apellidos.strip(),
                rol=rol,
                is_active=False,
            )
    except IntegrityError as error:
        if Usuario.objects.filter(email=email).exists():
            raise CorreoYaRegistrado from error
        raise

    invitacion = Invitacion.objects.create(
        usuario=usuario,
        creado_por=creado_por,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        expira_en=timezone.now() + timedelta(
            days=settings.INVITATION_TTL_DAYS,
        ),
    )
    return usuario, invitacion, token


@transaction.atomic
def aceptar_invitacion(token: str, password: str) -> Usuario:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    invitacion = (
        Invitacion.objects.select_for_update()
        .select_related('usuario')
        .filter(
            token_hash=token_hash,
            usado_en__isnull=True,
            expira_en__gt=timezone.now(),
        )
        .first()
    )
    if invitacion is None or invitacion.usuario.is_active:
        raise InvitacionNoValida

    usuario = invitacion.usuario
    validate_password(password, user=usuario)
    usuario.set_password(password)
    usuario.is_active = True
    usuario.save(update_fields=['password', 'is_active'])
    invitacion.usado_en = timezone.now()
    invitacion.save(update_fields=['usado_en'])
    return usuario


_CAMPOS_PRODUCTO = (
    'foto',
    'titulo',
    'origen',
    'precio',
    'descripcion',
    'url',
    'codigo_sku',
    'capacidad',
    'organizacion',
    'flag_visibilidad',
)


def _crear_version(
    catalogo: Catalogo,
    editor: Usuario,
    motivo: str,
    restaurada_desde: VersionCatalogo | None = None,
) -> VersionCatalogo:
    ultima_version = VersionCatalogo.objects.filter(
        catalogo=catalogo,
    ).aggregate(maximo=Max('numero'))['maximo']
    numero = (ultima_version or 0) + 1

    version = VersionCatalogo.objects.create(
        catalogo=catalogo,
        editor=editor,
        numero=numero,
        motivo=motivo,
        restaurada_desde=restaurada_desde,
    )
    ProductoVersion.objects.bulk_create(
        [
            ProductoVersion(
                version=version,
                producto_id_original=producto.pk,
                **{
                    campo: getattr(producto, campo)
                    for campo in _CAMPOS_PRODUCTO
                },
            )
            for producto in Producto.objects.filter(
                catalogo=catalogo,
            ).order_by('pk')
        ]
    )

    return version


@transaction.atomic
def guardar_version_catalogo(
    catalogo: Catalogo,
    editor: Usuario,
    motivo: str = '',
) -> VersionCatalogo:
    catalogo = Catalogo.objects.select_for_update().get(pk=catalogo.pk)
    return _crear_version(catalogo, editor, motivo)


@transaction.atomic
def restaurar_version_catalogo(
    version: VersionCatalogo,
    editor: Usuario,
    motivo: str = '',
) -> VersionCatalogo:
    version = VersionCatalogo.objects.get(pk=version.pk)
    catalogo = Catalogo.objects.select_for_update().get(
        pk=version.catalogo_id,
    )
    productos_guardados = list(
        version.productos.order_by('producto_id_original')
    )

    Producto.objects.filter(catalogo=catalogo).delete()
    Producto.objects.bulk_create(
        [
            Producto(
                catalogo=catalogo,
                **{
                    campo: getattr(producto, campo)
                    for campo in _CAMPOS_PRODUCTO
                },
            )
            for producto in productos_guardados
        ]
    )

    motivo_restauracion = motivo or f'Restauración de versión {version.numero}'
    return _crear_version(
        catalogo,
        editor,
        motivo_restauracion,
        restaurada_desde=version,
    )
