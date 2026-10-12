# Guía: despliegue local y secretos

Cómo completar el `.env`, levantar todo con Docker Compose, comprobar que funciona y ver el resultado del E2E (prueba de punta a punta) del CI (integración continua) sin desplegar nada. Para el detalle de cada pieza, el README.

> El `.env` nunca se sube al repo (está en `.gitignore`). Los valores de `.env.example` son de ejemplo: sirven en local, pero no se reutilizan en ningún servidor.

## 1. Variables de entorno

Primero copia el ejemplo:

```bash
cp .env.example .env
```

Con ese archivo tal cual, la página, la API y la base ya funcionan. El correo y el panel de administración quedan desactivados hasta que completes sus variables.

### Cómo generar un valor seguro

Para las claves y el secreto de sesión usa valores al azar:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # claves de la base
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # JWT_SECRET (64 caracteres)
```

`token_urlsafe` solo usa letras, números, `-` y `_`. Eso importa en las claves de la base, porque van dentro de una URL (`DATABASE_URL`) donde `@`, `:`, `/` o `#` la romperían.

### Base de datos

| Variable | Obligatoria | Qué es |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | No (por defecto `producto`) | Prefijo de los contenedores y del volumen de la base (`producto_db-data`). |
| `POSTGRES_USER` | Sí | Dueño de las tablas. Solo lo usan las migraciones (Alembic) y los tests, en el servicio `migrate`. |
| `POSTGRES_PASSWORD` | Sí | Clave del dueño. Genérala con `token_urlsafe(32)`. |
| `POSTGRES_DB` | Sí | Nombre de la base. |
| `APP_DB_USER` | Sí | Usuario de la API, que solo lee y escribe filas. Lo crea `db/init/01-usuario-api.sh`. Tiene que ser distinto de `POSTGRES_USER`. |
| `APP_DB_PASSWORD` | Sí | Clave del usuario de la API. Genérala con `token_urlsafe(32)`. |
| `DATABASE_URL` | Solo fuera de Docker | URL del usuario de la API, para correr la API o pytest desde tu máquina. Dentro de Docker, `compose.yml` la arma solo. |
| `MIGRATION_DATABASE_URL` | Solo fuera de Docker | URL del dueño, para Alembic y pytest desde tu máquina. |

Si cambias usuarios o claves de la base, actualiza también las dos URL, que repiten esos valores: `postgresql+psycopg://<usuario>:<clave>@localhost:<DB_PORT>/<POSTGRES_DB>`.

**Ojo:** Postgres crea los usuarios y sus claves solo la primera vez, cuando el volumen está vacío. Si cambias cualquiera de las variables `POSTGRES_*` o `APP_DB_*` después de haber levantado la base, tienes que recrearla (ver el paso 3).

### Correo del formulario de contacto (ADR 0005)

Opcionales. Si falta cualquiera de `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` o `CONTACT_NOTIFY_TO`, el mensaje igual se guarda y el log anota que el correo está desactivado.

| Variable | Qué es |
|---|---|
| `SMTP_HOST` | Servidor SMTP (protocolo de envío de correo). Con Gmail: `smtp.gmail.com`. |
| `SMTP_PORT` | Puerto. Por defecto `587`; la API usa STARTTLS con verificación del certificado. |
| `SMTP_USER` | Cuenta que envía (también va en el remitente). |
| `SMTP_PASSWORD` | Con Gmail, una **contraseña de aplicación**, nunca la clave normal. Se crea en la cuenta de Google, en Seguridad, y exige la verificación en dos pasos. |
| `CONTACT_NOTIFY_TO` | Dirección que recibe el aviso de cada mensaje. |

En local no hace falta completarlas: el formulario se prueba igual.

### Proxies de confianza

| Variable | Qué es |
|---|---|
| `TRUSTED_PROXIES` | IP o redes, separadas por coma, desde las que la API acepta `X-Forwarded-For` para saber la IP real del visitante. **En local se deja vacía.** En producción la fija `deploy/compose.prod.yml` en la red interna de Docker donde está Caddy. Vacía, nadie puede falsear su IP con ese header. |

### Administrador del panel (ADR 0004)

Opcionales para ver la página; obligatorias para usar el panel. Si falta alguna, `POST /api/admin/login` responde 503.

| Variable | Qué es | Cómo se genera |
|---|---|---|
| `ADMIN_EMAIL` | Correo con el que entras al panel. | Lo eliges. Cambiarlo cierra las sesiones abiertas. |
| `ADMIN_PASSWORD_HASH` | Hash Argon2 de la contraseña; la contraseña nunca se guarda. | `docker compose run --rm api python -m app.hash_password` (ver abajo). |
| `JWT_SECRET` | Firma la cookie de sesión (JWT, JSON Web Token). | `token_urlsafe(48)`. **Mínimo 32 caracteres**: si es más corto, la API no arranca. Cambiarlo cierra las sesiones abiertas. |

Para el hash:

```bash
docker compose run --rm api python -m app.hash_password
```

Pide la contraseña dos veces sin mostrarla (entre 12 y 256 caracteres) e imprime una línea así:

```
ADMIN_PASSWORD_HASH='$argon2id$v=19$m=...'
```

Pégala en el `.env` **tal cual, con las comillas simples**. El hash tiene varios `$`, y sin comillas simples Docker Compose los tomaría como variables y lo cortaría; el login fallaría siempre con 401.

### Puertos

| Variable | Por defecto | Qué es |
|---|---|---|
| `DB_PORT` | `5432` | Postgres en tu máquina. Si lo cambias, cámbialo también en las dos URL. |
| `API_PORT` | `8000` | API. |
| `WEB_PORT` | `5173` | Página (Vite). |

Cámbialos solo si el puerto ya está ocupado en tu máquina.

## 2. Levantar todo

Requisitos: Docker con Docker Compose v2 y Git.

```bash
cp .env.example .env        # si no lo hiciste
# completa el .env (sección 1)
docker compose up -d --build
```

Compose levanta, en orden:

1. `db`: Postgres 18. La primera vez corre `db/init/` y crea el usuario de la API.
2. `migrate`: aplica las migraciones (`alembic upgrade head`) y termina.
3. `api`: FastAPI en `:8000`, con recarga al cambiar `api/app/`.
4. `web`: Vite en `:5173`, con recarga al cambiar `web/`. Pasa `/api` a la API.

`--build` solo hace falta la primera vez o si cambiaste `api/pyproject.toml` o `web/package.json`.

## 3. Después de cambiar variables

| Cambiaste | Qué correr |
|---|---|
| Correo, administrador, `JWT_SECRET`, `TRUSTED_PROXIES` | `docker compose up -d`. Compose recrea los contenedores cuya configuración cambió. |
| Puertos | `docker compose up -d`. |
| `POSTGRES_*` o `APP_DB_*` | `docker compose down -v && docker compose up -d`. |

`down -v` borra el volumen de la base, y con él **todos los datos locales**. Es necesario porque Postgres solo crea usuarios y claves al iniciar una base vacía: con la base vieja, la API seguiría intentando entrar con la clave nueva y fallaría. En local no hay datos que importen, pero nunca lo corras contra un servidor real.

Para apagar sin borrar nada: `docker compose down`.

## 4. Verificar que funciona

```bash
docker compose ps                                 # db y api "healthy" o "running"; migrate "exited (0)"
curl -i http://localhost:8000/api/health          # 200 si la API y la base responden; 503 si la base no
```

- Abre http://localhost:5173: la página muestra el estado de la API como "ok". Eso prueba el camino completo: página, proxy, API y base.
- http://localhost:8000/docs tiene la documentación interactiva de la API.
- Si configuraste el administrador, prueba el login (reemplaza el correo y la contraseña; no la dejes en el historial de un servidor compartido):

  ```bash
  curl -i -X POST http://localhost:8000/api/admin/login \
    -H "Content-Type: application/json" \
    -d '{"email": "tu-correo", "password": "tu-contraseña"}'
  ```

  200 con una cabecera `set-cookie: admin_session=...` es que funciona. 401 es correo o contraseña incorrectos (o el hash sin comillas simples), 503 es que falta alguna de las tres variables y 429 es que se pasó el límite de 5 intentos fallidos en 15 minutos.

Si algo falla, mira los logs: `docker compose logs api` (o `migrate`, `db`, `web`). Los problemas más comunes:

| Síntoma | Causa probable |
|---|---|
| `migrate` termina con error y la API no arranca | La base tiene claves distintas a las del `.env`: recréala (paso 3). |
| La API se cae con un error de validación de `jwt_secret` | `JWT_SECRET` tiene menos de 32 caracteres. |
| `port is already allocated` | Ese puerto está ocupado: cambia `DB_PORT`, `API_PORT` o `WEB_PORT`. |
| La página dice algo distinto de "ok" | Revisa `/api/health` y `docker compose logs api`. |

### Tests en local

```bash
docker compose run --rm migrate pytest -q --cov=app --cov-fail-under=80   # API
cd web && npm ci && npx playwright install chromium && npm run e2e         # E2E, con el compose arriba
```

## 5. Ver sin desplegar: el E2E del CI

No hace falta levantar nada en tu máquina para saber si la página funciona: cada PR (pull request) y cada push a `dev` y `main` corre el job **E2E** de `.github/workflows/ci.yml`, que levanta todo en una máquina desechable de GitHub.

Qué hace el job:

1. Copia `.env.example` a `.env` (valores de ejemplo, sin secretos; el CI no usa ninguno) y levanta la base, las migraciones y la API con `docker compose up -d --build --wait api`.
2. Instala Chromium y corre Playwright (`npm run e2e`), que arranca `npm run dev` y abre la página en un navegador real.
3. Revisa tres cosas (`web/e2e/`):
   - la página abre, muestra el título y el estado de la API dice "ok" (página, proxy, API y base);
   - la respuesta trae las cabeceras de seguridad definidas en `web/security-headers.ts`;
   - la consola del navegador no muestra errores.
4. Si algo falla, imprime los logs de todos los contenedores del compose.

Como corre sin el administrador ni el correo configurados, no prueba el login ni el envío de correos; esos los cubre pytest en el job API.

Dónde ver los resultados:

- **En el PR:** al final de la conversación, en la lista de checks, la fila **ci / E2E** queda en verde o en rojo. "Details" abre el log.
- **En Actions:** pestaña **Actions** del repo, workflow **ci**, la corrida del commit y el job **E2E**. En el paso `npm run e2e` está cada test con su resultado; si uno falla, Playwright además deja una anotación con el error en el resumen de la corrida.
- **Si falló:** el paso "Logs del compose si falla" tiene los logs de la base, las migraciones y la API. En el CI, Playwright reintenta una vez cada test que falla; si pasa al reintentarlo, el job queda verde, pero el resumen lo cuenta como inestable (flaky).

El CI no guarda capturas ni videos de la página. Para verla con tus ojos hay que levantarla en local (sección 2) o esperar al despliegue en staging (hito 1 del plan).
