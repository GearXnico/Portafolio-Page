"""Visit recording and the panel's visit counts.

Anyone controls what arrives in the URL or the headers, so it is cleaned and trimmed before
saving it. The visit is never rejected because of that: the page has to load even if the
link carries garbage.
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

# The same limits as the constraints of the `visit` table.
UTM_MAX_LENGTH = 200
REFERRER_MAX_LENGTH = 2048
# The user agent only goes into the hash; it is trimmed so megabytes aren't hashed.
USER_AGENT_MAX_LENGTH = 512

# Unicode: control, format (invisible), surrogates, private use, unassigned, and line and
# paragraph separators.
_REMOVED_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"})

_VALID_HOST = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$")


def clean_text(value: str | None, max_length: int) -> str | None:
    """Remove control and invisible characters, trim spaces and length. Empty becomes None.

    The removed categories include the null byte (Postgres doesn't accept it in a `text`), line
    breaks (also U+2028 and U+2029) and the characters that reverse the text direction, which
    could disguise a value in the panel or break a CSV export.
    """
    if value is None:
        return None
    # Trim before filtering so huge values aren't walked; the margin covers removed characters.
    cleaned = "".join(
        c for c in value[: max_length * 4] if unicodedata.category(c) not in _REMOVED_CATEGORIES
    )
    cleaned = cleaned.strip()[:max_length].strip()
    return cleaned or None


def referrer_origin(referrer: str | None) -> str | None:
    """Keep only the origin (`https://domain`) of the page the visitor came from.

    The full URL can carry personal data (searches, emails, tokens); the domain is enough to
    know where the visit comes from.
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
    """Return the salt for `day`, creating it if it doesn't exist, and delete earlier days' salts.

    Usually it already exists and reading it is enough. Only the first visit of the day writes;
    if two arrive at once, `ON CONFLICT DO NOTHING` leaves a single salt.
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
    """HMAC-SHA256 of IP and user agent, as 64 hexadecimal characters."""
    message = f"{ip}\n{user_agent[:USER_AGENT_MAX_LENGTH]}".encode()
    return hmac.new(salt, message, hashlib.sha256).hexdigest()


def count_by_utm(session: Session) -> list[VisitCountOut]:
    """Visits and unique visitors by `utm_source` and `utm_campaign`, most visited first.

    Visits without UTM parameters fall in the group with both set to
    `null` (direct traffic), which goes last in a tie.
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
