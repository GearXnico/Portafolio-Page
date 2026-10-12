# Referencia de la API

Qué hace cada ruta de la API, qué valida y cómo se protege. Para levantarla y correr sus tests, el README; para el porqué de cada decisión, `docs/adr/`.

La documentación interactiva, generada desde el código, está en http://localhost:8000/docs con el compose arriba.

## Primera carga y visitas: `GET /api/bootstrap`

La página llama a `GET /api/bootstrap` al abrirse. La API registra la visita, decide el idioma y devuelve todo el contenido visible en una sola respuesta, con `Cache-Control: no-store`.

Parámetros (todos opcionales; el frontend los pasa en la tarea 3.5):

| Parámetro | Qué es | Cómo se guarda |
|---|---|---|
| `utm_source`, `utm_medium`, `utm_campaign`, `utm_content` | UTM (parámetros de origen del enlace) | Sin caracteres de control ni invisibles y recortados a 200 caracteres. Nunca hacen fallar la página. |
| `referrer` | `document.referrer` de la página | Solo el dominio (`https://www.linkedin.com`); la URL completa puede traer datos personales. |
| `lang` | Idioma elegido en el selector | Manda sobre el navegador. Si no es `es` ni `en`, se ignora. |

Respuesta:

```json
{
  "lang": "es",
  "profile": {"headline_es": "", "headline_en": "", "about_es": "", "about_en": "", "links": {"github": "https://…"}},
  "skills": [{"name": "Python", "category": "language"}],
  "experience": [{"company": "", "role_es": "", "role_en": "", "description_es": "", "description_en": "", "start_date": "2024-01-01", "end_date": null}],
  "projects": [{"slug": "", "title_es": "", "title_en": "", "summary_es": "", "summary_en": "", "body_es": "", "body_en": "", "stack": [], "demo_url": null, "repo_url": null, "images": [{"url": "/media/…", "alt_es": "", "alt_en": ""}]}]
}
```

- **Idioma** (`app/services/locale.py`, ADR 0002): el primero de `Accept-Language`, que el navegador pone como preferido. Español si es `es`; si no, o si no viene el header, inglés.
- **Contenido**: textos en los dos idiomas, para que el selector cambie sin otra llamada. `profile` es `null` mientras no se cargue el perfil. Solo salen los proyectos con `visible = true`. No salen ids, orden, visibilidad, fechas de edición ni el correo de contacto.
- **Visitante único por día**: no se guarda la IP. Se guarda un HMAC-SHA256 (hash con clave) de IP y user agent, cuya clave es una sal al azar que se crea cada día (UTC) en la tabla `visitor_salt` y se borra al día siguiente. Sin la sal, ni con un respaldo de la base se puede volver a la IP.
- Si falla el registro de la visita, la página igual carga.

En producción la API está detrás de Caddy: `deploy/compose.prod.yml` fija `TRUSTED_PROXIES` en la red interna de Docker donde está Caddy, para que la API lea la IP real de `X-Forwarded-For`. Sin eso, todos los visitantes compartirían la IP de Caddy y el conteo de únicos bajaría.

## Formulario de contacto

`POST /api/contact` recibe `name`, `email`, `message`, `lang` (`es` o `en`) y, si vienen, `utm_source` y `utm_campaign`. Guarda el mensaje y responde 201; después, en segundo plano, avisa por correo con SMTP (`app/services/mail.py`, ADR 0005) y marca `emailed`. Si el correo falla o no está configurado, el mensaje igual queda guardado y el log lo anota, solo con el id del mensaje.

Contra el spam y los abusos:

- **Validación:** largos máximos iguales a los de la tabla (200, 320 y 5.000 caracteres), correo con formato válido, sin caracteres de control ni saltos de línea fuera del mensaje (así nadie puede inyectar cabeceras en el correo) y sin campos extra. Responde 422 si algo no calza.
- **Honeypot (campo trampa):** el formulario debe incluir un campo `website` oculto. Si llega con algo, es un bot: la API responde 201 igual, pero no guarda nada.
- **Límite por IP:** 5 mensajes por hora; después responde 429 con `Retry-After`. Vive en memoria del proceso, así que la API corre con un solo proceso de Uvicorn. En producción, `TRUSTED_PROXIES` tiene que incluir a Caddy para que el límite vea la IP real y no la del proxy.
- **Tamaño:** la API rechaza cuerpos de más de 64 KB (413) y los que no declaran su largo (411).
- **Al mostrarlo:** la API guarda el texto tal cual y nunca lo interpreta. El correo va en texto plano y la web lo muestra como texto (React lo escapa); nunca con `dangerouslySetInnerHTML`.

## Login del administrador

El panel tiene un solo usuario (ADR 0004), sin tabla: sus credenciales van en el `.env`.

1. Genera el hash de la contraseña (mínimo 12 caracteres): `docker compose run --rm api python -m app.hash_password`. Copia la línea `ADMIN_PASSWORD_HASH='...'` al `.env` tal cual, con las comillas simples.
2. Completa `ADMIN_EMAIL` y `JWT_SECRET` (al menos 32 caracteres al azar: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`).
3. Reinicia la API: `docker compose up -d api`.

| Ruta | Qué hace |
|---|---|
| `POST /api/admin/login` | Recibe `email` y `password`. Si calzan, deja la cookie `admin_session` y responde 200; si no, 401. Sin configuración, 503. |
| `POST /api/admin/logout` | Borra la cookie (204). |
| `GET /api/admin/session` | 200 con sesión, 401 sin ella. |

Toda ruta nueva de `/api/admin/*` va en `router` de `app/routers/admin.py`, que exige sesión por defecto; solo el login y el logout van en `public_router`. Un test recorre todas las rutas de `/api/admin/*` y falla si alguna responde sin sesión.

- **Contraseña:** hash Argon2 (`argon2-cffi`). La contraseña se verifica aunque el correo esté mal, para que el tiempo de respuesta no diga cuál falló.
- **Sesión:** JWT (JSON Web Token) firmado con HS256 y `JWT_SECRET`, de 7 días, en una cookie `httpOnly`, `Secure`, `SameSite=Strict` y con `path=/api/admin`. Cambiar `JWT_SECRET` cierra todas las sesiones; cambiar `ADMIN_EMAIL` también.
- **Límite:** 5 intentos fallidos cada 15 minutos por IP; después responde 429 con `Retry-After`. Un login correcto borra los intentos de esa IP. Usa el mismo límite en memoria y `TRUSTED_PROXIES` que el formulario de contacto.

## Contenido desde el panel

Rutas para editar lo que muestra la página. Todas exigen la sesión del administrador (sin ella, 401 antes de mirar el cuerpo) y usan JSON, salvo la subida de capturas, que es un formulario (multipart). Los cambios se ven en la siguiente carga de `GET /api/bootstrap`.

| Recurso | Rutas |
|---|---|
| Proyectos | `GET` y `POST /api/admin/projects`; `GET`, `PUT` y `DELETE /api/admin/projects/{id}` |
| Capturas | `POST /api/admin/projects/{id}/images` (campos `file`, `alt_es` y `alt_en`); `DELETE /api/admin/projects/{id}/images/{image_id}` |
| Perfil | `GET` y `PUT /api/admin/profile` (el primer `PUT` lo crea; antes, `GET` responde 404) |
| Habilidades | `GET` y `POST /api/admin/skills`; `PUT` y `DELETE /api/admin/skills/{id}` |
| Experiencia | `GET` y `POST /api/admin/experience`; `PUT` y `DELETE /api/admin/experience/{id}` |

- **Orden y visibilidad:** cada elemento tiene `position` (el menor va primero). Un proyecto nuevo queda oculto (`visible: false`) hasta que se publica con un `PUT`. El panel ve también los ocultos.
- **`PUT` reemplaza todo:** manda el objeto completo; lo que no llega toma su valor por defecto.
- **Validación:** campos de más (como `id`), caracteres de control, largos sobre el máximo y enlaces que no sean `https://` responden 422. Un slug repetido responde 409 y un id que no existe, 404.
- **Capturas:** JPEG, PNG o WebP de hasta 5 MB, reconocidos por su contenido y no por la extensión. La API las vuelve a codificar como WebP (máximo 2560 px por lado, sin metadatos como el GPS de una foto ni el perfil de color: una captura en Display P3 se verá un poco menos saturada), con un nombre al azar, en `MEDIA_DIR/projects/` (por defecto `media/`, un volumen en Docker). Cada proyecto las trae en `images`, con su `url` en `/media/...`. Responde 413 si pesa más de 5 MB, 415 si no es una imagen aceptada y 422 si está dañada o pasa los 25 megapíxeles. Sin sesión, la subida responde 401 antes de leer el archivo.
- **Al borrar un proyecto o una captura** se borran las filas y los archivos.

## Base de datos: dos usuarios

La API no se conecta como dueña de las tablas. Hay dos usuarios de Postgres:

| Usuario | Variable | Puede | Lo usa |
|---|---|---|---|
| Dueño (`POSTGRES_USER`) | `MIGRATION_DATABASE_URL` | Crear, cambiar y borrar tablas | Solo el servicio `migrate` (Alembic y los tests) |
| API (`APP_DB_USER`) | `DATABASE_URL` | Leer, insertar, actualizar y borrar filas | La API |

Así, un error o una inyección de SQL en la API no puede borrar ni cambiar tablas. El usuario de la API lo crea `db/init/01-usuario-api.sh` la primera vez que arranca la base. Si tu base local es anterior a ese script, recréala con `docker compose down -v && docker compose up -d` (borra los datos locales). Los tests de `tests/test_permisos_db.py` comprueban estos límites.
