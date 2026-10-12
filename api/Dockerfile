# Imagen de producción de la API (deploy/compose.prod.yml). La de desarrollo es Dockerfile.dev.

# 1. Instala solo las dependencias de producción en un entorno virtual.
FROM python:3.14-slim AS build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /code
COPY pyproject.toml ./
COPY app ./app
# Al final saca pip: no hace falta para correr la app y trae CVE en las librerías que copia.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install . \
    && /opt/venv/bin/pip uninstall -y pip

# 2. Imagen final: el entorno virtual, las migraciones y un usuario sin privilegios.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

# Sin pip en la imagen final. /media guarda las capturas (volumen compartido con Caddy).
RUN python -m pip uninstall -y pip \
    && useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /media \
    && chown app:app /media

WORKDIR /code
COPY --from=build /opt/venv /opt/venv
# Alembic corre desde esta misma imagen, en el servicio `migrate` de compose.prod.yml.
COPY alembic.ini ./
COPY alembic ./alembic

USER app
EXPOSE 8000
# Sin log de acceso, porque anota la IP de cada visitante (dato personal), y sin cabecera Server.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--no-server-header"]
