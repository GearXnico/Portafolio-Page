"""Guardado del contenido que se edita desde el panel de administración."""

from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException, status
from psycopg.errors import UniqueViolation
from pydantic import BaseModel
from sqlalchemy import ColumnExpressionArgument, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, Profile

# Nombre de la restricción única del slug (convención de nombres de app/models/base.py).
_SLUG_CONSTRAINT = "uq_project_slug"


def list_ordered[M: Base](
    session: Session, model: type[M], *order_by: ColumnExpressionArgument[Any]
) -> Sequence[M]:
    return session.scalars(select(model).order_by(*order_by)).all()


def get_or_404[M: Base](session: Session, model: type[M], item_id: int) -> M:
    item = session.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe.")
    return item


def create[M: Base](session: Session, model: type[M], data: BaseModel) -> M:
    item = model(**data.model_dump())
    session.add(item)
    _commit(session)
    return item


def update[M: Base](session: Session, item: M, data: BaseModel) -> M:
    """Reemplaza todos los campos editables (PUT): lo que no llega toma su valor por defecto."""
    for field, value in data.model_dump().items():
        setattr(item, field, value)
    _commit(session)
    return item


def delete(session: Session, item: Base) -> None:
    session.delete(item)
    session.commit()


def save_profile(session: Session, data: BaseModel) -> Profile:
    """Crea el perfil la primera vez y después lo reemplaza. Siempre es la fila 1.

    Un solo `INSERT ... ON CONFLICT`: dos guardados seguidos (doble clic) no chocan.
    """
    values = data.model_dump()
    statement = (
        insert(Profile)
        .values(id=1, **values)
        .on_conflict_do_update(
            index_elements=[Profile.id], set_=values | {"updated_at": func.now()}
        )
        .returning(Profile)
    )
    profile = session.scalars(statement).one()
    session.commit()
    return profile


def _commit(session: Session) -> None:
    """Guarda los cambios. Un slug repetido responde 409; cualquier otro error sigue su curso."""
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        orig = exc.orig
        if isinstance(orig, UniqueViolation) and orig.diag.constraint_name == _SLUG_CONSTRAINT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un proyecto con ese slug.",
            ) from exc
        raise
