from django.db import transaction
from django.db.models import Max

from catalogo.models import (
    Catalogo,
    Producto,
    ProductoVersion,
    Usuario,
    VersionCatalogo,
)


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
