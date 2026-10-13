"""First load of the page: records the visit and returns all the visible content."""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import Experience, Profile, Project, Skill, Visit
from app.schemas.bootstrap import (
    Bootstrap,
    PublicExperience,
    PublicImage,
    PublicProfile,
    PublicProject,
    PublicSkill,
)
from app.services.locale import Lang, decide_locale, parse_lang
from app.services.visits import (
    UTM_MAX_LENGTH,
    clean_text,
    daily_salt,
    referrer_origin,
    visitor_hash,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["bootstrap"])


# The parameters have no length limit on purpose: a link with UTM (Urchin Tracking Module,
# the link's source parameters) values that are too long or odd is cleaned and trimmed,
# instead of responding 422 and leaving the visitor without a page.
@router.get("/bootstrap", response_model=Bootstrap)
def bootstrap(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    accept_language: Annotated[str | None, Header()] = None,
    user_agent: Annotated[str | None, Header()] = None,
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    utm_content: str | None = None,
    lang: str | None = None,
    referrer: str | None = None,
) -> Bootstrap:
    """Record the visit and return the language, the profile and the visible content.

    - `lang`: the language the visitor chose in the selector (the frontend stores it); it wins
      over the browser's. If it is neither `es` nor `en`, it is ignored.
    - `referrer`: the page's `document.referrer`. Only its domain is saved.
    """
    # The country will come from Cloudflare (ADR (Architecture Decision Record) 0002); for now
    # it isn't known.
    country = None
    page_lang = parse_lang(lang) or decide_locale(country, accept_language)
    content = _visible_content(session, page_lang)

    try:
        with session.begin_nested():
            salt = daily_salt(session, datetime.now(UTC).date())
            session.add(
                Visit(
                    lang=page_lang,
                    # Behind Caddy, the real IP arrives with TRUSTED_PROXIES (ADR 0004).
                    visitor_hash=visitor_hash(
                        salt, request.client.host if request.client else "", user_agent or ""
                    ),
                    referrer=referrer_origin(referrer),
                    country=country,
                    utm_source=clean_text(utm_source, UTM_MAX_LENGTH),
                    utm_medium=clean_text(utm_medium, UTM_MAX_LENGTH),
                    utm_campaign=clean_text(utm_campaign, UTM_MAX_LENGTH),
                    utm_content=clean_text(utm_content, UTM_MAX_LENGTH),
                )
            )
        session.commit()
    except SQLAlchemyError:
        # If recording fails, the page is still shown. `begin_nested` already rolled back the
        # visit and the session closes when the request ends. The log carries no visitor data.
        logger.exception("Could not record the visit")

    # Each load is a visit: no intermediate cache must store this response.
    response.headers["Cache-Control"] = "no-store"
    return content


def _visible_content(session: Session, page_lang: Lang) -> Bootstrap:
    profile = session.get(Profile, 1)
    skills = session.scalars(select(Skill).order_by(Skill.position, Skill.id))
    experience = session.scalars(
        select(Experience).order_by(
            Experience.position, Experience.start_date.desc(), Experience.id
        )
    )
    projects = session.scalars(
        select(Project)
        .where(Project.visible.is_(True))
        .order_by(Project.position, Project.id)
        .options(selectinload(Project.images))
    )
    return Bootstrap(
        lang=page_lang,
        profile=PublicProfile.model_validate(profile) if profile else None,
        skills=[PublicSkill.model_validate(s) for s in skills],
        experience=[PublicExperience.model_validate(e) for e in experience],
        projects=[
            PublicProject(
                slug=p.slug,
                title_es=p.title_es,
                title_en=p.title_en,
                summary_es=p.summary_es,
                summary_en=p.summary_en,
                body_es=p.body_es,
                body_en=p.body_en,
                stack=p.stack,
                demo_url=p.demo_url,
                repo_url=p.repo_url,
                images=[
                    PublicImage(url=f"/media/{i.path}", alt_es=i.alt_es, alt_en=i.alt_en)
                    for i in p.images
                ],
            )
            for p in projects
        ],
    )
