"""Registro de visitas (limpia lo que manda el visitante y calcula el hash diario) y sus conteos
para el panel.

Lo que llega en la URL o en los headers lo controla cualquiera, así que se limpia y se
recorta antes de guardarlo. Nunca se rechaza la visita por eso: la página tiene que cargar
aunque el enlace traiga basura.
"""

import hashlib
import hmac
import re
import secrets
import unicodedata
from datetime import date
from urllib.parse import urlsplit

from sqlalchemy import delete, distinct, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.visit import Visit
from app.models.visitor_salt import SALT_BYTES, VisitorSalt
from app.schemas.visits import VisitCountOut

# Los mismos límites que las restricciones de la tabla `visit`.
UTM_MAX_LENGTH = 200
REFERRER_MAX_LENGTH = 2048
# El user agent solo entra al hash; se recorta para no hashear megabytes.
USER_AGENT_MAX_LENGTH = 512

# Unicode: control, formato (invisibles), sustitutos, uso privado, sin asignar, y separadores
# de línea y de párrafo.
_REMOVED_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"})

_VALID_HOST = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$")


def clean_text(value: str | None, max_length: int) -> str | None:
    """Quita caracteres de control e invisibles, recorta espacios y largo. Vacío pasa a None.

    Las categorías quitadas incluyen el byte nulo (Postgres no lo acepta en un `text`), los
    saltos de línea (también U+2028 y U+2029) y los caracteres que invierten la dirección del
    texto, que podrían disfrazar un valor en el panel o romper un export CSV.
    """
    if value is None:
        return None
    # Se recorta antes de filtrar, para no recorrer un valor de muchos KB (kilobytes). El margen
    # deja espacio a los caracteres que el filtro quita.
    cleaned = "".join(
        c for c in value[: max_length * 4] if unicodedata.category(c) not in _REMOVED_CATEGORIES
    )
    cleaned = cleaned.strip()[:max_length].strip()
    return cleaned or None


def referrer_origin(referrer: str | None) -> str | None:
    """Deja solo el origen (`https://dominio`) de la página de la que vino el visitante.

    La URL completa puede traer datos personales (búsquedas, correos, tokens); para saber de
    dónde viene la visita basta con el dominio.
    """
    if not referrer or len(referrer) > REFERRER_MAX_LENGTH:
        return None
    try:
        parts = urlsplit(referrer.strip())
        host = parts.hostname
        port = parts.port
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or not host or not _VALID_HOST.match(host):
        return None
    return f"{parts.scheme}://{host}" + (f":{port}" if port else "")


def daily_salt(session: Session, day: date) -> bytes:
    """Devuelve la sal de `day`, creándola si no existe, y borra las de días anteriores.

    Lo normal es que ya exista y basta con leerla. Solo la primera visita del día escribe; si
    dos llegan a la vez, `ON CONFLICT DO NOTHING` deja una sola sal.
    """
    query = select(VisitorSalt.salt).where(VisitorSalt.day == day)
    salt = session.scalars(query).one_or_none()
    if salt is not None:
        return salt
    session.execute(
        insert(VisitorSalt)
        .values(day=day, salt=secrets.token_bytes(SALT_BYTES))
        .on_conflict_do_nothing(index_elements=[VisitorSalt.day])
    )
    session.execute(delete(VisitorSalt).where(VisitorSalt.day < day))
    return session.scalars(query).one()


def visitor_hash(salt: bytes, ip: str, user_agent: str) -> str:
    """HMAC-SHA256 (hash con clave) de IP y user agent, en hexadecimal de 64 caracteres."""
    message = f"{ip}\n{user_agent[:USER_AGENT_MAX_LENGTH]}".encode()
    return hmac.new(salt, message, hashlib.sha256).hexdigest()


def count_by_utm(session: Session) -> list[VisitCountOut]:
    """Visitas y visitantes únicos por `utm_source` y `utm_campaign`, las más visitadas primero.

    Las visitas sin UTM salen en el grupo con los dos en `null` (tráfico directo), que en un
    empate va al final.
    """
    visits = func.count().label("visits")
    query = (
        select(
            Visit.utm_source,
            Visit.utm_campaign,
            visits,
            func.count(distinct(Visit.visitor_hash)).label("unique_visitors"),
        )
        .group_by(Visit.utm_source, Visit.utm_campaign)
        .order_by(visits.desc(), Visit.utm_source, Visit.utm_campaign)
    )
    return [
        VisitCountOut.model_validate(row, from_attributes=True) for row in session.execute(query)
    ]
