"""Lo que llega al sitio, visto desde el panel: mensajes de contacto y visitas por UTM.

Todas las rutas exigen la sesión del administrador (`require_admin`, en el router completo).
Los mensajes traen datos personales del remitente; las visitas salen solo como conteos.
"""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import ContactMessage
from app.routers.admin import require_admin
from app.schemas.contact import ContactMessageOut, MessageReadIn
from app.schemas.visits import VisitCountOut
from app.services import contact, visits

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])

DbSession = Annotated[Session, Depends(get_session)]
# Los ids son `integer` de Postgres: uno fuera de rango sería un error 500 en la base.
MessageId = Annotated[int, Path(ge=1, le=2**31 - 1)]


@router.get("/messages", response_model=list[ContactMessageOut])
def list_messages(session: DbSession) -> Sequence[ContactMessage]:
    return contact.list_messages(session)


@router.patch("/messages/{message_id}", response_model=ContactMessageOut)
def mark_message(
    message_id: MessageId, payload: MessageReadIn, session: DbSession
) -> ContactMessage:
    """Marca el mensaje como leído (`{"read": true}`) o no leído. 404 si no existe."""
    return contact.set_read(session, message_id, payload.read)


@router.get("/visits")
def count_visits(session: DbSession) -> list[VisitCountOut]:
    return visits.count_by_utm(session)
