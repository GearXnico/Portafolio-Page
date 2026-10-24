# Production image of the API (deploy/compose.prod.yml). The development one is Dockerfile.dev.

# 1. Install only the production dependencies in a virtual environment.
FROM python:3.14-slim AS build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /code
COPY pyproject.toml ./
COPY app ./app
# Remove pip at the end: the app doesn't need it to run, and it brings CVEs in the libraries it vendors.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install . \
    && /opt/venv/bin/pip uninstall -y pip

# 2. Final image: the virtual environment, the migrations and an unprivileged user.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

# No pip in the final image. /media stores the screenshots (volume shared with Caddy).
RUN python -m pip uninstall -y pip \
    && useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /media \
    && chown app:app /media

WORKDIR /code
COPY --from=build /opt/venv /opt/venv
# Alembic runs from this same image, in the `migrate` service of compose.prod.yml.
COPY alembic.ini ./
COPY alembic ./alembic

USER app
EXPOSE 8000
# No access log, because it records each visitor's IP (personal data), and no Server header.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--no-server-header"]
