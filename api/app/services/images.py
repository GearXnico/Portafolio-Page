"""Project screenshots: validation, conversion to WebP and files in the media folder.

Security:
- The format is detected from the file's content, never from its name or its Content-Type.
- The image is re-encoded as WebP: what is saved is not the uploaded file but new pixels,
  without metadata (EXIF with GPS, for example) or hidden content.
- The server generates the file name; the original name is discarded.
"""

import io
import logging
import threading
from collections.abc import Iterable
from typing import BinaryIO
from uuid import uuid4

from fastapi import HTTPException, status
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Project, ProjectImage

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ACCEPTED_FORMATS = ("JPEG", "PNG", "WEBP")
# An image small in bytes can take up gigabytes when opened (decompression bomb). 25 MP
# covers a 6K screenshot (21 MP) and is checked before decoding the pixels.
MAX_PIXELS = 25_000_000
# A 25 MP image takes ~100 MB decoded, and the conversion makes copies. At most two
# conversions at a time bound the memory even if several uploads arrive together.
_conversions = threading.Semaphore(2)
# Longest side of the saved image: enough for a large screen and light to load.
MAX_SIDE = 2560
WEBP_QUALITY = 85
FOLDER = "projects"


def add_image(
    session: Session,
    project: Project,
    file: BinaryIO,
    size: int | None,
    alt_es: str,
    alt_en: str,
) -> ProjectImage:
    """Convert the image to WebP, save it to disk and add it at the end of the project."""
    if size is None or size > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="The screenshot exceeds 5 MB.",
        )
    with _conversions:
        data = to_webp(file)

    relative_path = f"{FOLDER}/{uuid4().hex}.webp"
    file_path = settings.media_dir / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    # "x" never overwrites an existing file.
    with file_path.open("xb") as output:
        output.write(data)

    try:
        # Lock the project until the commit: two simultaneous uploads don't take the same
        # position. It is locked after converting, so nobody is held up during the conversion.
        session.execute(select(Project.id).where(Project.id == project.id).with_for_update())
        position = session.scalar(
            select(func.coalesce(func.max(ProjectImage.position), -1) + 1).where(
                ProjectImage.project_id == project.id
            )
        )
        image = ProjectImage(
            project_id=project.id,
            path=relative_path,
            alt_es=alt_es,
            alt_en=alt_en,
            position=position,
        )
        session.add(image)
        session.commit()
    except Exception:
        # Without a row in the database, the file would be orphaned.
        session.rollback()
        file_path.unlink(missing_ok=True)
        raise
    return image


def to_webp(file: BinaryIO) -> bytes:
    try:
        image = Image.open(file, formats=ACCEPTED_FORMATS)
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The file is not a JPEG, PNG or WebP image.",
        ) from exc
    except Image.DecompressionBombError as exc:
        raise _too_many_pixels() from exc

    with image:
        # Image.open only read the header: the size is known without decoding the pixels.
        if image.width * image.height > MAX_PIXELS:
            raise _too_many_pixels()
        try:
            # Rotate the image according to its EXIF (phone photos) before discarding the metadata.
            converted = ImageOps.exif_transpose(image)
            converted.thumbnail((MAX_SIDE, MAX_SIDE))
            converted = converted.convert("RGBA" if converted.has_transparency_data else "RGB")
            output = io.BytesIO()
            # No `exif` or `icc_profile`: the WebP comes out without metadata.
            converted.save(output, format="WEBP", quality=WEBP_QUALITY)
        # Pillow raises different errors depending on the format and the file damage.
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="The image is damaged or can't be read.",
            ) from exc
    return output.getvalue()


def _too_many_pixels() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="The screenshot has too many pixels (maximum 25 megapixels).",
    )


def delete_image(session: Session, image: ProjectImage) -> None:
    path = image.path
    session.delete(image)
    session.commit()
    remove_files([path])


def remove_files(paths: Iterable[str]) -> None:
    """Delete the files after deleting their rows.

    If a file can't be deleted, the row no longer exists and the page doesn't show it: only an
    orphaned file remains on disk, which is noted in the log.
    """
    for path in paths:
        try:
            (settings.media_dir / path).unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not delete the screenshot %s", path)
