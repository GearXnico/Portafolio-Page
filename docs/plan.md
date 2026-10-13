# Plan · Sitio web de portafolio

ID: 2026-10-08-sitio-portafolio · Versión: borrador 3 (2026-10-12) · Base: `brief.md`, `architecture.md` y `adr/`

## Resumen

Este plan es solo del **sitio de portafolio**. El repositorio nació como `plantilla-producto`, pero el código de los hitos 2 y 3 ya es el portafolio, así que se renombró a `Portafolio-Page` y aquí se termina (decisión de Nicolas, 2026-10-12). La plantilla reutilizable se hace después, como un proyecto aparte, extrayendo lo que de verdad se repite.

El orden general del trabajo (decisión de Nicolas, 2026-10-12) es este:

1. **Terminar el desarrollo del portafolio:** hitos 3 y 4 de este plan.
2. **Crear la plantilla** como proyecto nuevo, con su propio brief y plan, a partir del portafolio terminado.
3. **Uno o dos proyectos rápidos** creados desde la plantilla, que después se muestran en el portafolio.
4. **Recién entonces, el gasto:** el hito 5 de este plan despliega el portafolio, y los otros productos se despliegan en el mismo VPS (servidor virtual privado).

Los puntos 2 y 3 no son parte de este plan: cada uno tendrá sus propios documentos. La plantilla es parte del ecosistema (Nicolas, 2026-10-12), así que no ocupa el cupo de idea activa; los proyectos rápidos sí siguen las reglas de activación.

**El desarrollo no tiene costo.** Los hitos 0 a 4 usan solo herramientas gratis: GitHub, Actions en un repo público y Docker en local. El hito 5 contrata los servidores y el dominio. El hito 1 ya armó las imágenes de producción y las prueba en CI (integración continua) con `deploy-check` (el staging efímero de la ADR 0008), así que en el hito 5 quedan solo los servidores, el DNS (sistema de nombres de dominio), los secretos y el `deploy.yml`.

**Las fechas son una guía**, para ver si vamos bien, no plazos (Nicolas, 2026-10-12).

Cada tarea está pensada para terminarse en una sesión de Claude Code. Se entrega como una rama `feature/*`, `fix/*`, `docs/*` o `chore/*` con su PR (pull request) a `dev`, según la ADR (registro de decisión de arquitectura) 0007. "Terminado" significa que se cumple el criterio de la tabla y la checklist de terminado de esa ADR. Cada tarea parte con un prompt hecho desde `prompts/template.md` y queda en `prompts/log.md` (ADR 0009).

| Hito | Entrega | Horas | Estado |
|---|---|---|---|
| 0 | Accesos gratuitos listos | 2 | Terminado |
| 1 | Base con CI, seguridad y prueba de despliegue en CI | 22,5 | Terminado (1.9 en este PR) |
| 2 | API y base de datos | 14 | Terminado |
| 3 | Frontend público bilingüe | 17 | 3.1 y 3.2 terminadas |
| 4 | Panel de administración | 18 | Pendiente |
| 5 | Despliegue, contenido y publicación de la versión 1 (~US$13,20 al mes más $9.990 al año por el dominio) | 20,5 | Después de la plantilla y los proyectos rápidos |
| | **Total** | **94** | |

Quedan ~28 h de desarrollo (3.3 a 3.6 y el hito 4) y las 20,5 h del hito 5.

## Hito 0 · Accesos gratuitos (lo haces tú, sin Claude Code)

**Terminado el 2026-10-11:** contraseña de Gmail, repo `plantilla-producto` (público, `dev` por defecto, con acceso de Claude), cuotas revisadas (Actions y GHCR gratis en repos públicos) y token generado.

| # | Tarea | Horas | Terminado cuando |
|---|---|---|---|
| 0.1 | Crear la contraseña de aplicación de Gmail (requiere verificación en dos pasos) | 0,5 | La tienes guardada en tu gestor de contraseñas |
| 0.2 | Crear el repo público `plantilla-producto` en GitHub, vacío y con `dev` como rama por defecto | 0,5 | El repo existe y Claude Code tiene acceso |
| 0.3 | Revisar con Claude Code las cuotas gratuitas de GitHub Actions y GHCR (el registro de imágenes de GitHub) para repos públicos | 0,5 | No hay sorpresas de costo |
| 0.4 | Generar `CLAUDE_CODE_OAUTH_TOKEN` con `claude setup-token`, para la revisión automática | 0,5 | Tienes el token guardado |

## Hito 1 · Base con CI y prueba de despliegue, sin costo

El repo se llamó `plantilla-producto` porque al principio iba a ser la plantilla. La tarea 1.9 lo renombró a `Portafolio-Page`; ya no se marca como "template repository". El repo vacío que se llamaba `portfolio-page` quedó como `Product-template`, para la futura plantilla.

| # | Tarea | Horas | Terminado cuando |
|---|---|---|---|
| 1.1 | Estructura del monorepo (`api/`, `web/`, `deploy/`), `compose.yml` local, README, `.env.example`, `.gitignore` y plantilla de PR | 2 | `docker compose up` levanta todo en local |
| 1.2 | Esqueleto de la API: FastAPI, `GET /api/health` que consulta la base, Alembic iniciado, pytest contra Postgres, `ruff` y `mypy` | 3 | Los tests pasan en local y `/api/health` responde 200 |
| 1.3 | Esqueleto web: Vite, React y TypeScript estricto, ESLint, Prettier, Vitest y un E2E (prueba de punta a punta) con Playwright que abre la página | 3 | Los tests y el E2E pasan en local |
| 1.4 | `ci.yml`: jobs de API y web en paralelo, caché, mínimos de cobertura (80 % y 60 %) y `pre-commit` | 3 | Un PR de prueba muestra todos los checks en verde, y un test roto lo deja en rojo |
| 1.5 | Seguridad en CI: CodeQL, reglas de seguridad de `ruff`, `pip-audit`, `npm audit`, Trivy y `dependabot.yml` | 3 | Los checks corren en el PR; una dependencia vulnerable de prueba lo bloquea |
| 1.6 | Imágenes de producción: Dockerfiles multi-stage de la API y de Caddy (con el build de web dentro), `compose.prod.yml` (con red interna fija y `TRUSTED_PROXIES` apuntando a ella, ADR 0004), Caddyfile y job `deploy-check` en CI, con respaldo y migraciones como en producción | 4 | `deploy-check` levanta el compose de producción en el runner, aplica las migraciones y pasa el E2E |
| 1.7 | Reglas de GitHub: rulesets de `main` y `dev` (1 aprobación con bypass tuyo, historial lineal, solo rebase & merge, checks obligatorios) y `sync-dev.yml`. El gate de staging se agrega en el hito 5. | 3 | Un PR sin checks en verde no se puede mergear, y después de un PR de versión de prueba `dev` queda sincronizada |
| 1.8 | `ai-review.yml`: revisión automática con IA en los PR a `dev`, con `CLAUDE_CODE_OAUTH_TOKEN` (ADR 0007) | 1 | Un PR de prueba recibe comentarios del revisor y el PR de documentación se salta |
| 1.9 | Renombre. **Lo hiciste tú (2026-10-12):** `plantilla-producto` pasó a `Portafolio-Page` y el repo vacío `portfolio-page` pasó a `Product-template` (GitHub conserva el historial, los PR y una redirección desde los nombres viejos). **Con Claude Code:** actualizar el README, `architecture.md` (sección 7), el brief (punto 8 y la métrica de la plantilla pasan al proyecto de la plantilla) y este plan | 0,5 | El CI corre en verde y ningún documento presenta este repo como la plantilla |

**Fin del hito:** cada PR pasa por tests, seguridad, revisión con IA y una prueba del despliegue completo en CI, todo sin costo, en el repo `Portafolio-Page`.

## Hito 2 · API y base de datos

| # | Tarea | Horas | Terminado cuando |
|---|---|---|---|
| 2.1 | Modelos y migración inicial: perfil, habilidades, experiencia, proyectos, imágenes, visitas y mensajes | 2 | `alembic upgrade head` crea las 7 tablas, con tests de restricciones |
| 2.2 | `GET /api/bootstrap`: registra la visita con UTM (parámetros de origen del enlace) y hash diario, decide el idioma y devuelve el contenido visible | 3 | Tests de idioma (es, en y sin header), de UTM y de proyectos ocultos |
| 2.3 | Login del administrador: Argon2, JWT (token firmado) en cookie, límite de intentos y comando para generar el hash | 3 | Tests de login correcto, incorrecto, bloqueo y acceso sin sesión a `/api/admin/*` |
| 2.4 | CRUD (crear, leer, actualizar y borrar) de administración: proyectos (con orden y visibilidad), perfil, habilidades y experiencia | 3 | Tests de cada ruta, con cobertura de la API ≥ 80 % |
| 2.5 | Subida de capturas: máximo 5 MB, conversión a WebP y guardado en `/media` | 1,5 | Tests con imagen válida, archivo muy grande y archivo que no es imagen |
| 2.6 | Contacto: guarda el mensaje, honeypot, límite por IP (dirección de red) y correo en tarea de fondo | 1,5 | Tests de envío, spam bloqueado y correo fallido que igual guarda el mensaje |

## Hito 3 · Frontend público

| # | Tarea | Horas | Terminado cuando |
|---|---|---|---|
| 3.1 | Layout de una página: perfil, habilidades, experiencia, proyectos y contacto, responsive | 4 | Se ve bien en un celular y en escritorio, con tests de render |
| 3.2 | Idiomas: textos fijos en JSON, idioma según `bootstrap`, selector y `localStorage` | 3 | E2E: con el navegador en inglés sale en inglés, y el selector cambia y se recuerda |
| 3.3 | Sección de proyectos con capturas, stack y enlaces a demo y repositorio | 3 | Los proyectos ocultos no aparecen; tests de componente |
| 3.4 | Formulario de contacto con validación y mensajes de éxito y error en los dos idiomas | 3 | E2E: un mensaje enviado aparece en la base |
| 3.5 | UTM: se leen de la URL (dirección web) y se pasan a `bootstrap` y al contacto | 1 | E2E: una visita con UTM queda registrada con su origen |
| 3.6 | SEO (posicionamiento en buscadores) y accesibilidad: títulos, `meta` por idioma, `hreflang` y contraste | 3 | Lighthouse ≥ 90 en accesibilidad y SEO |

## Hito 4 · Panel de administración

| # | Tarea | Horas | Terminado cuando |
|---|---|---|---|
| 4.1 | Ruta `/admin` con login, logout y protección de rutas | 3 | E2E: sin sesión redirige al login |
| 4.2 | Lista y edición de proyectos: formulario con los dos idiomas lado a lado, orden y ocultar | 5 | E2E: crear un proyecto y verlo en la página pública |
| 4.3 | Subida de capturas desde el formulario de proyecto | 2 | E2E: la captura se ve en la página pública |
| 4.4 | Edición de perfil, habilidades y experiencia | 4 | E2E: un cambio de perfil se ve en la página |
| 4.5 | Mensajes de contacto (marcar como leído) y visitas agrupadas por `utm_source` y `utm_campaign` | 3 | Se ven los mensajes y los conteos de una visita de prueba con UTM |
| 4.6 | Prueba de la meta del brief: agregar un proyecto real cronometrado | 1 | Toma menos de 10 minutos |

## Hito 5 · Despliegue, contenido y publicación (aquí empieza el gasto)

Se inicia cuando el hito 4 está terminado y probado en local y en CI, **y además** la plantilla y al menos un proyecto rápido están terminados (orden decidido por Nicolas el 2026-10-12). Antes de empezar, se revisa cómo comparten el VPS y Caddy los productos que haya.

| # | Tarea | Horas | Terminado cuando |
|---|---|---|---|
| 5.1 | Crear la cuenta en DigitalOcean con alerta de facturación y tu llave SSH (acceso remoto cifrado), y registrar el dominio .cl en NIC Chile ($9.990 al año). Lo haces tú. | 1 | Puedes crear un droplet y el dominio está a tu nombre |
| 5.2 | Servidores de staging y producción: droplets, usuario `deploy`, `ufw`, `unattended-upgrades`, Docker, DNS, `staging.<dominio>` con usuario, contraseña y `noindex` | 4 | `ssh deploy@` funciona en los dos y Caddy responde con HTTPS (conexión cifrada) |
| 5.3 | `deploy.yml` y `deploy/deploy.sh` por ambiente: respaldo, migraciones, cambio de contenedores, health check y rollback; botón manual por SHA (identificador del commit). Se activa el gate de staging en el ruleset de `main`. | 4,5 | Un merge a `dev` despliega staging, un health check roto a propósito vuelve solo a la versión anterior y el PR a `main` exige staging en verde |
| 5.4 | `backup.sh` con cron, respaldo semanal de DigitalOcean activo y prueba de restauración | 1 | Restauraste un respaldo en staging y los datos coinciden |
| 5.5 | Cargar el perfil, las habilidades y la experiencia en los dos idiomas, desde el panel en producción | 3 | El contenido está completo en `es` y `en` |
| 5.6 | Escribir el caso de la propia página: arquitectura, pipeline, y qué hizo la IA y qué decidiste tú | 3 | El proyecto está publicado con capturas y enlace al repo |
| 5.7 | Repaso final en staging: E2E completos, prueba en celular y restauración de respaldo | 2 | Todo en verde y sin errores en los logs |
| 5.8 | PR de versión a `main`, etiqueta `v1.0.0` y enlaces con UTM para las próximas postulaciones | 2 | El sitio está público y tienes 5 enlaces listos para usar |

## Riesgos del plan

| Riesgo | Señal | Qué hacer |
|---|---|---|
| El despliegue real, el área menos practicada, queda para el final | Las tareas 5.2 o 5.3 pasan de 4 h cada una | `deploy-check` ya probó las imágenes, el compose y las migraciones en el hito 1, así que lo que queda es servidor, DNS y secretos. Si se traba, se publica primero solo producción y staging se suma unos días después. |
| El portafolio tarda en publicarse porque el hito 5 espera a la plantilla y a los proyectos rápidos | Pasan semanas con el portafolio terminado y sin publicar | Decisión consciente para ahorrar costos. Si una postulación lo necesita antes, se puede adelantar el hito 5 solo para el portafolio. |
| El panel crece | El hito 4 pasa de 18 h | Se publica sin el reorden de proyectos (4.2) y sin las visitas por UTM (4.5); se agregan después |
| La futura plantilla no puede actualizar al portafolio | Al crear la plantilla | Aceptado: el portafolio no se sincroniza con la plantilla. Si después conviene, se conecta con un merge único y se resuelven los conflictos una vez. |

## Después de la versión 1

- Métrica del brief: agregar más de 1 desarrollo nuevo en el primer mes.
- Detección de idioma por país con Cloudflare (ADR 0002).
- Revisión de las métricas de visitas por postulación a las 8 semanas.
- Agregar al portafolio los proyectos rápidos hechos con la plantilla, cada uno con su caso.
