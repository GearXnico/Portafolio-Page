"""Estado de la API y de su conexión a la base."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    """Responde 200 si la API está arriba y la base contesta; 503 si la base no contesta."""
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no responde",
        ) from exc
    return {"status": "ok", "database": "ok"}
