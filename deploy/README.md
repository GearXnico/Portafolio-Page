# deploy/

Archivos de producción y staging. Las imágenes son `api/Dockerfile` (la API) y `web/Dockerfile` (Caddy con el build de la página y el `Caddyfile` de esta carpeta).

| Archivo | Tarea | Qué hace |
|---|---|---|
| `compose.prod.yml` | 1.6 | Base, migraciones, API y Caddy, sin root, sin capabilities, con el sistema de archivos de solo lectura, límites de memoria y logs que rotan |
| `Caddyfile` | 1.6 | HTTPS automático, la página, `/media`, `/api` y las mismas cabeceras de seguridad de `web/security-headers.ts` |
| `deploy.sh` | 5.3 | Respaldo, migraciones, health check y rollback |
| `backup.sh` | 5.4 | `pg_dump` diario |

## Probarlo en tu máquina

Es lo mismo que hace el job `deploy-check` de CI (integración continua) en cada PR:

```bash
cp .env.example deploy/.env
# En deploy/.env: SITE_ADDRESS=http://localhost (solo HTTP), y ADMIN_EMAIL, ADMIN_PASSWORD_HASH
# y JWT_SECRET, que producción exige (cómo generarlos, en .env.example).
docker compose -f deploy/compose.prod.yml --env-file deploy/.env up -d --build --wait caddy
cd web && E2E_BASE_URL=http://localhost npm run e2e
docker compose -f deploy/compose.prod.yml --env-file deploy/.env down -v   # borra la base de prueba
```

Usa los puertos 80 y 443, así que no lo levantes junto a otro servidor web.

## Dónde van los secretos

El `.env` nunca se sube al repo, que es público.

- **En CI:** `deploy-check` usa las claves de ejemplo de `.env.example` y valores de prueba para el administrador, porque la base se destruye al terminar. No necesita secretos de GitHub.
- **En staging y producción (hito 5):** cada servidor tiene su propio `deploy/.env`, junto a `compose.prod.yml`, con permisos `600` y dueño el usuario `deploy`. Lo creas tú una vez por SSH (acceso remoto cifrado) y no cambia con cada despliegue. Lleva las variables de `.env.example` con valores nuevos y al azar (no los de tu máquina), más `SITE_ADDRESS` con el dominio. Staging y producción no comparten claves.
- **En GitHub (hito 5):** solo lo que necesita el workflow de despliegue para entrar al servidor: la llave SSH, el host y el usuario, como secretos del ambiente `staging` o `production` (ADR 0008).

En el servidor, además de `deploy/`, tiene que estar `db/init/`, que crea el usuario de la API la primera vez que arranca la base.

## Decisiones de esta carpeta

- **Red interna fija** (`172.30.0.0/24`): `TRUSTED_PROXIES` apunta a ella, así que la API solo lee `X-Forwarded-For` de Caddy (ADR 0004). Caddy reemplaza ese header por la IP real del visitante.
- **Sin root:** la API corre con el usuario `app` (uid 10001), Caddy con `caddy` (uid 10002) y Postgres con `postgres`. A Caddy se le quita el permiso de abrir puertos bajos, porque Docker ya los deja abrir sin privilegios.
- **Memoria** para el VPS (servidor virtual privado) de 1 GiB: base 384 MiB, API 256 MiB y Caddy 128 MiB, en total 768 MiB.
- **Sin logs de acceso:** ni Uvicorn ni Caddy anotan la IP de cada visita, porque es un dato personal.
- **Migraciones:** el servicio `migrate` corre antes de que cambie la API, y es el único con la clave del dueño de las tablas.
