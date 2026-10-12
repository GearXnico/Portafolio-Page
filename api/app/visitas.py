"""Registro de visitas: limpia lo que manda el visitante y calcula el hash diario.

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

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.visitor_salt import SALT_BYTES, VisitorSalt

# Los mismos límites que las restricciones de la tabla `visit`.
UTM_MAX_LENGTH = 200
REFERRER_MAX_LENGTH = 2048
# El user agent solo entra al hash; se recorta para no hashear megabytes.
USER_AGENT_MAX_LENGTH = 512

_HOST_VALIDO = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$")


def limpiar_texto(valor: str | None, largo_maximo: int) -> str | None:
    """Quita caracteres de control e invisibles, recorta espacios y largo. Vacío pasa a None.

    Los caracteres de las categorías Unicode "C" incluyen el byte nulo (Postgres no lo acepta
    en un `text`), saltos de línea y los que invierten la dirección del texto, que podrían
    disfrazar un valor en el panel.
    """
    if valor is None:
        return None
    limpio = "".join(c for c in valor if not unicodedata.category(c).startswith("C"))
    limpio = limpio.strip()[:largo_maximo].strip()
    return limpio or None


def origen_del_referrer(referrer: str | None) -> str | None:
    """Deja solo el origen (`https://dominio`) de la página de la que vino el visitante.

    La URL completa puede traer datos personales (búsquedas, correos, tokens); para saber de
    dónde viene la visita basta con el dominio.
    """
    if not referrer or len(referrer) > REFERRER_MAX_LENGTH:
        return None
    try:
        partes = urlsplit(referrer.strip())
        host = partes.hostname
        puerto = partes.port
    except ValueError:
        return None
    if partes.scheme not in ("http", "https") or not host or not _HOST_VALIDO.match(host):
        return None
    return f"{partes.scheme}://{host}" + (f":{puerto}" if puerto else "")


def sal_del_dia(session: Session, dia: date) -> bytes:
    """Devuelve la sal de `dia`, creándola si no existe, y borra las de días anteriores.

    Si dos visitas llegan a la vez, `ON CONFLICT DO NOTHING` deja una sola sal.
    """
    session.execute(
        insert(VisitorSalt)
        .values(day=dia, salt=secrets.token_bytes(SALT_BYTES))
        .on_conflict_do_nothing(index_elements=[VisitorSalt.day])
    )
    session.execute(delete(VisitorSalt).where(VisitorSalt.day < dia))
    return session.scalars(select(VisitorSalt.salt).where(VisitorSalt.day == dia)).one()


def hash_visitante(sal: bytes, ip: str, user_agent: str) -> str:
    """HMAC-SHA256 (hash con clave) de IP y user agent, en hexadecimal de 64 caracteres."""
    mensaje = f"{ip}\n{user_agent[:USER_AGENT_MAX_LENGTH]}".encode()
    return hmac.new(sal, mensaje, hashlib.sha256).hexdigest()
