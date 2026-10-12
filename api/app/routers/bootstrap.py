"""Primera carga de la página: registra la visita y entrega todo el contenido visible."""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.idioma import Idioma, decidir_idioma, es_idioma
from app.models import Experience, Profile, Project, Skill, Visit
from app.schemas.bootstrap import (
    Bootstrap,
    CapturaPublica,
    ExperienciaPublica,
    HabilidadPublica,
    PerfilPublico,
    ProyectoPublico,
)
from app.visitas import (
    UTM_MAX_LENGTH,
    hash_visitante,
    limpiar_texto,
    origen_del_referrer,
    sal_del_dia,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["bootstrap"])

# Los parámetros llegan sin límite de largo a propósito: un enlace con UTM (parámetros de
# origen del enlace) demasiado largos o raros se limpia y se recorta, en vez de responder 422
# y dejar al visitante sin página.
Texto = str | None


@router.get("/bootstrap", response_model=Bootstrap)
def bootstrap(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    accept_language: Annotated[str | None, Header()] = None,
    user_agent: Annotated[str | None, Header()] = None,
    utm_source: Texto = None,
    utm_medium: Texto = None,
    utm_campaign: Texto = None,
    utm_content: Texto = None,
    lang: Texto = None,
    referrer: Texto = None,
) -> Bootstrap:
    """Registra la visita y devuelve el idioma, el perfil y el contenido visible.

    - `lang`: el idioma que el visitante eligió en el selector (lo guarda el frontend); manda
      sobre el del navegador. Si no es `es` ni `en`, se ignora.
    - `referrer`: el `document.referrer` de la página. Solo se guarda su dominio.
    """
    idioma: Idioma = es_idioma(lang) or decidir_idioma(accept_language)
    contenido = _contenido_visible(session, idioma)

    try:
        with session.begin_nested():
            _registrar_visita(
                session,
                idioma=idioma,
                ip=request.client.host if request.client else "",
                user_agent=user_agent or "",
                utm={
                    "utm_source": utm_source,
                    "utm_medium": utm_medium,
                    "utm_campaign": utm_campaign,
                    "utm_content": utm_content,
                },
                referrer=referrer,
            )
        session.commit()
    except SQLAlchemyError:
        # Si falla el registro, la página igual se muestra. No se registran los datos del
        # visitante en el log.
        session.rollback()
        logger.exception("No se pudo registrar la visita")

    # Cada carga es una visita: ningún caché intermedio debe guardar esta respuesta.
    response.headers["Cache-Control"] = "no-store"
    return contenido


def _contenido_visible(session: Session, idioma: Idioma) -> Bootstrap:
    perfil = session.get(Profile, 1)
    habilidades = session.scalars(select(Skill).order_by(Skill.position, Skill.id))
    experiencia = session.scalars(
        select(Experience).order_by(
            Experience.position, Experience.start_date.desc(), Experience.id
        )
    )
    proyectos = session.scalars(
        select(Project)
        .where(Project.visible.is_(True))
        .order_by(Project.position, Project.id)
        .options(selectinload(Project.images))
    )
    return Bootstrap(
        lang=idioma,
        profile=PerfilPublico.model_validate(perfil) if perfil else None,
        skills=[HabilidadPublica.model_validate(h) for h in habilidades],
        experience=[ExperienciaPublica.model_validate(e) for e in experiencia],
        projects=[
            ProyectoPublico(
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
                    CapturaPublica(url=f"/media/{i.path}", alt_es=i.alt_es, alt_en=i.alt_en)
                    for i in p.images
                ],
            )
            for p in proyectos
        ],
    )


def _registrar_visita(
    session: Session,
    *,
    idioma: Idioma,
    ip: str,
    user_agent: str,
    utm: dict[str, str | None],
    referrer: str | None,
) -> None:
    sal = sal_del_dia(session, datetime.now(UTC).date())
    session.add(
        Visit(
            lang=idioma,
            visitor_hash=hash_visitante(sal, ip, user_agent),
            referrer=origen_del_referrer(referrer),
            # El país llegará desde Cloudflare (ADR 0002); por ahora no se conoce.
            country=None,
            **{campo: limpiar_texto(valor, UTM_MAX_LENGTH) for campo, valor in utm.items()},
        )
    )
    session.flush()
