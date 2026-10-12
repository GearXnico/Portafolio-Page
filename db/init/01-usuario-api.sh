#!/bin/sh
# Crea el usuario con el que se conecta la API, con permisos mínimos.
#
# - POSTGRES_USER es el dueño de las tablas y corre las migraciones (Alembic).
# - APP_DB_USER solo puede leer y escribir filas: no crea, borra ni vacía tablas,
#   así que un error o una inyección de SQL en la API no puede cambiar el esquema.
#
# Postgres corre los scripts de /docker-entrypoint-initdb.d solo cuando el volumen
# de la base está vacío. Si ya tenías la base, recréala con `docker compose down -v`.
set -eu

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -v owner="$POSTGRES_USER" \
    -v db="$POSTGRES_DB" \
    -v app_user="$APP_DB_USER" \
    -v app_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

-- Nadie más que el dueño y la API se conecta a esta base.
REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"db" TO :"app_user";

-- Usa el esquema, pero no crea objetos en él.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO :"app_user";

-- Las tablas y secuencias que creen las migraciones le dan solo estos permisos.
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO :"app_user";
SQL
