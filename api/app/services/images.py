"""Capturas de los proyectos: validación, conversión a WebP y archivos en la carpeta de media.

Seguridad:
- El formato se detecta por el contenido del archivo, nunca por su nombre ni su Content-Type.
- La imagen se vuelve a codificar como WebP: lo que se guarda no es el archivo subido, sino
  píxeles nuevos, sin metadatos (EXIF con GPS, por ejemplo) ni contenido escondido.
- El nombre del archivo lo genera el servidor; el nombre original se descarta.
"""

import io
import logging
import threading
from collections.abc import Iterable
from typing import BinaryIO
from uuid import uuid4

from fastapi import HTTPException, status
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Project, ProjectImage

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
# Formatos que se aceptan, según el contenido del archivo.
ACCEPTED_FORMATS = ("JPEG", "PNG", "WEBP")
# Una imagen chica en bytes puede ocupar gigas al abrirla (bomba de descompresión). 25 MP
# cubre una captura 6K (21 MP) y se revisa antes de decodificar los píxeles.
MAX_PIXELS = 25_000_000
# Una imagen de 25 MP ocupa ~100 MB decodificada, y la conversión hace copias. Como mucho dos
# conversiones a la vez acotan la memoria aunque lleguen varias subidas juntas.
_conversions = threading.Semaphore(2)
# Lado mayor de la imagen guardada: suficiente para una pantalla grande y liviana de cargar.
MAX_SIDE = 2560
WEBP_QUALITY = 85
# Subcarpeta dentro de la carpeta de media.
FOLDER = "projects"


def add_image(
    session: Session,
    project: Project,
    file: BinaryIO,
    size: int | None,
    alt_es: str,
    alt_en: str,
) -> ProjectImage:
    """Convierte la imagen a WebP, la guarda en disco y la agrega al final del proyecto."""
    if size is None or size > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="La captura supera los 5 MB.",
        )
    with _conversions:
        data = to_webp(file)

    relative_path = f"{FOLDER}/{uuid4().hex}.webp"
    file_path = settings.media_dir / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    # "x": falla si el archivo ya existe, en vez de pisarlo.
    with file_path.open("xb") as output:
        output.write(data)

    image = ProjectImage(
        project_id=project.id,
        path=relative_path,
        alt_es=alt_es,
        alt_en=alt_en,
        position=max((i.position for i in project.images), default=-1) + 1,
    )
    session.add(image)
    try:
        session.commit()
    except Exception:
        # Sin fila en la base, el archivo quedaría huérfano.
        file_path.unlink(missing_ok=True)
        raise
    return image


def to_webp(file: BinaryIO) -> bytes:
    try:
        image = Image.open(file, formats=ACCEPTED_FORMATS)
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="El archivo no es una imagen JPEG, PNG o WebP.",
        ) from exc
    except Image.DecompressionBombError as exc:
        raise _too_many_pixels() from exc

    with image:
        # Image.open solo leyó la cabecera: el tamaño se conoce sin decodificar los píxeles.
        if image.width * image.height > MAX_PIXELS:
            raise _too_many_pixels()
        try:
            # Gira la imagen según su EXIF (fotos de celular) antes de descartar los metadatos.
            converted = ImageOps.exif_transpose(image)
            converted.thumbnail((MAX_SIDE, MAX_SIDE))
            converted = converted.convert("RGBA" if converted.has_transparency_data else "RGB")
            output = io.BytesIO()
            # Sin `exif` ni `icc_profile`: el WebP sale sin metadatos.
            converted.save(output, format="WEBP", quality=WEBP_QUALITY)
        # Pillow lanza errores distintos según el formato y el daño del archivo.
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="La imagen está dañada o no se puede leer.",
            ) from exc
    return output.getvalue()


def _too_many_pixels() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="La captura tiene demasiados píxeles (máximo 25 megapíxeles).",
    )


def delete_image(session: Session, image: ProjectImage) -> None:
    path = image.path
    session.delete(image)
    session.commit()
    remove_files([path])


def remove_files(paths: Iterable[str]) -> None:
    """Borra los archivos después de borrar sus filas.

    Si un archivo no se puede borrar, la fila ya no existe y la página no lo muestra: solo
    queda un archivo huérfano en disco, que se anota en el log.
    """
    for path in paths:
        try:
            (settings.media_dir / path).unlink(missing_ok=True)
        except OSError:
            logger.warning("No se pudo borrar la captura %s", path)
