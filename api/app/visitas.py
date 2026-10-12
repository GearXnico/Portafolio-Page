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

# Unicode: control, formato (invisibles), sustitutos, uso privado, sin asignar, y separadores
# de línea y de párrafo.
_CATEGORIAS_QUITADAS = frozenset({"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"})

_HOST_VALIDO = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$")


def limpiar_texto(valor: str | None, largo_maximo: int) -> str | None:
    """Quita caracteres de control e invisibles, recorta espacios y largo. Vacío pasa a None.

    Las categorías quitadas incluyen el byte nulo (Postgres no lo acepta en un `text`), los
    saltos de línea (también U+2028 y U+2029) y los caracteres que invierten la dirección del
    texto, que podrían disfrazar un valor en el panel o romper un export CSV.
    """
    if valor is None:
        return None
    # Se recorta antes de filtrar, para no recorrer un valor de muchos KB (kilobytes). El margen
    # deja espacio a los caracteres que el filtro quita.
    limpio = "".join(
        c for c in valor[: largo_maximo * 4] if unicodedata.category(c) not in _CATEGORIAS_QUITADAS
    )
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

    Lo normal es que ya exista y basta con leerla. Solo la primera visita del día escribe; si
    dos llegan a la vez, `ON CONFLICT DO NOTHING` deja una sola sal.
    """
    consulta = select(VisitorSalt.salt).where(VisitorSalt.day == dia)
    sal = session.scalars(consulta).one_or_none()
    if sal is not None:
        return sal
    session.execute(
        insert(VisitorSalt)
        .values(day=dia, salt=secrets.token_bytes(SALT_BYTES))
        .on_conflict_do_nothing(index_elements=[VisitorSalt.day])
    )
    session.execute(delete(VisitorSalt).where(VisitorSalt.day < dia))
    return session.scalars(consulta).one()


def hash_visitante(sal: bytes, ip: str, user_agent: str) -> str:
    """HMAC-SHA256 (hash con clave) de IP y user agent, en hexadecimal de 64 caracteres."""
    mensaje = f"{ip}\n{user_agent[:USER_AGENT_MAX_LENGTH]}".encode()
    return hmac.new(sal, mensaje, hashlib.sha256).hexdigest()
