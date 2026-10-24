#!/bin/sh
# Creates the user the API connects with, with least privilege.
#
# - POSTGRES_USER owns the tables and runs the migrations (Alembic).
# - APP_DB_USER can only read and write rows: it can't create, drop or truncate tables,
#   so a bug or an SQL injection in the API can't change the schema.
#
# Postgres runs the scripts in /docker-entrypoint-initdb.d only when the database
# volume is empty. If you already had the database, recreate it with `docker compose down -v`.
set -eu

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -v owner="$POSTGRES_USER" \
    -v db="$POSTGRES_DB" \
    -v app_user="$APP_DB_USER" \
    -v app_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

-- Nobody but the owner and the API connects to this database.
REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"db" TO :"app_user";

-- It uses the schema, but doesn't create objects in it.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO :"app_user";

-- Tables and sequences created by the migrations grant it only these privileges.
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner" IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO :"app_user";
SQL
