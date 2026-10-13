# 0007 · Flujo de trabajo, testing y seguridad

Estado: aceptada · Fecha: 2026-10-11 · Pidió: Nicolas

## Contexto

Nicolas pidió estas reglas para el repo del sitio, que después hereda la plantilla:

- Testing obligatorio para aprobar en `dev`, automatizado con CI/CD (integración y despliegue continuos).
- Validación de seguridad.
- Ramas `feature/nombre-descriptivo`.
- PR (pull request) con aprobación, y más adelante un check de despliegue.
- Buenas prácticas de desarrollo y de control de versiones.
- En la revisión agregó dos pedidos: un ambiente de staging, que se resuelve en la ADR 0008, y que todo merge a `dev` o `main` sea con rebase & merge, para tener un historial de commits más claro.

Esta ADR (registro de decisión de arquitectura) reemplaza la regla "solo `main`" de la 0006.

Hay una limitación de GitHub: el autor de un PR no puede aprobarlo. Los PR que abre Claude quedan a nombre de Nicolas, así que una aprobación obligatoria los bloquearía. Nicolas eligió cómo resolverlo el 2026-10-11.

## Opciones consideradas

Sobre el modelo de ramas:

| Opción | Costo | Contras |
|---|---|---|
| A. Solo `main` con ramas cortas (lo que proponía la 0006) | El más bajo | Sin una rama donde integrar y probar antes de publicar |
| B. `dev` para integración y `main` para producción, con ramas `feature/*` desde `dev` | Un PR extra por versión publicada | Hay que mantener `dev` y `main` sincronizadas |
| C. Git Flow completo (ramas `release/*` y `hotfix/*` permanentes) | Varios PR por versión | Excesivo para una persona |

Sobre la aprobación obligatoria:

| Opción | Costo | Contras |
|---|---|---|
| A. Tu merge es la aprobación: PR y checks obligatorios, sin aprobaciones | Ninguno | No queda una aprobación formal en GitHub |
| B. 1 aprobación obligatoria con bypass solo para ti: mergeas marcando "bypass" y GitHub lo registra | Un clic extra por PR | La aprobación es tu acción explícita, no la de otra persona |
| C. Una segunda cuenta (bot o colaborador) que aprueba | ~1 h y una cuenta más | Aprobar con otra cuenta tuya es solo un trámite |

## Decisión

- **Modelo de ramas: B**, porque es lo que pidió Nicolas.
- **Aprobación: B, 1 aprobación con bypass registrado** (Nicolas, 2026-10-11). `main` y `dev` exigen 1 aprobación, y solo Nicolas puede saltársela, marcando el bypass al mergear; GitHub registra cada bypass. Cuando los agentes de la fábrica abran PR con su propia cuenta, Nicolas los aprobará de forma normal.

### Ramas y control de versiones

| Rama | Sale de | Entra a | Para qué |
|---|---|---|---|
| `main` | — | — | Lo publicado. Cada merge despliega a producción. |
| `dev` | `main` | `main` por PR de versión | Integración. Es la rama por defecto del repo, y cada merge despliega a staging (ADR 0008). |
| `feature/<nombre-descriptivo>` | `dev` | `dev` | Funcionalidad nueva, por ejemplo `feature/formulario-contacto` |
| `fix/<nombre>` | `dev` | `dev` | Corrección |
| `docs/<nombre>`, `chore/<nombre>` | `dev` | `dev` | Documentación, configuración y dependencias |
| `hotfix/<nombre>` | `main` | `main` y después `dev` | Corrección urgente en producción |

Los nombres van en minúsculas, separados con guiones, en español y de 2 a 4 palabras.

1. **Commits:** se usa Conventional Commits (formato estándar de mensajes), por ejemplo `feat: agrega formulario de contacto` o `fix: corrige idioma por defecto`. Los tipos son `feat`, `fix`, `test`, `docs`, `refactor` y `chore`.
2. **PR a `dev`:**
   - Uno por funcionalidad, idealmente con menos de ~400 líneas cambiadas.
   - Usa la plantilla del repo: Antes, Después, Cómo probar y la checklist de terminado.
   - Merge con **rebase & merge**: los commits de la rama se copian uno a uno sobre `dev`, sin merge commits, y el historial queda lineal.
   - Como cada commit llega tal cual, antes de abrir el PR se ordenan con `git rebase -i`: cada commit hace una sola cosa, sigue Conventional Commits y deja los tests en verde.
   - La rama se borra después del merge.
3. **PR de versión `dev` → `main`:** también con **rebase & merge**. Exige que staging esté sano con el mismo SHA (ADR 0008). Después del despliegue se crea una etiqueta SemVer (versionado semántico, `v1.2.0`) con las notas de la versión en `CHANGELOG.md`.
   - **Ojo:** GitHub vuelve a escribir cada commit al hacer rebase & merge, así que en `main` quedan con SHA (identificador) distinto que en `dev`. Si no se corrige, el siguiente PR de versión muestra commits repetidos o conflictos.
   - Para evitarlo, el workflow `sync-dev.yml` corre después de cada push a `main` y hace `git rebase main` sobre `dev`. Git descarta solo los commits que ya están en `main` y conserva los nuevos. Después hace `git push --force-with-lease` a `dev`. Es el único actor con bypass de la regla "sin force push" en `dev`.
   - Un `hotfix/*` entra a `main` y llega a `dev` por ese mismo workflow.
4. **Versiones** (Nicolas, 2026-10-13): cada PR mergeado a `dev` tiene una versión con formato SemVer (`MAJOR.MINOR.PATCH`) y la anota en `CHANGELOG.md`. Un PR `feat` sube MINOR y uno de otro tipo sube PATCH. MAJOR cuenta las publicaciones a `main` y sigue en `0` hasta la primera, `1.0.0`. La guía, con un ejemplo, está al final de `CHANGELOG.md`.
4. **Protección de `main` y `dev`:**
   - Sin force push ni borrado (salvo `sync-dev.yml` en `dev`).
   - Historial lineal obligatorio, y rebase & merge como único método de merge habilitado.
   - PR obligatorio con 1 aprobación; el bypass queda permitido solo para Nicolas.
   - Los checks de abajo tienen que estar en verde.
   - La rama tiene que estar al día con su base antes de mergear.
   - En tu propia rama `feature/*` se permite `git push --force-with-lease`.
5. **Nunca en el repo:** `.env`, llaves ni datos reales. Se versiona solo `.env.example`.

### Testing (requisito para mergear en `dev`)

| Nivel | Herramienta | Qué cubre | Regla |
|---|---|---|---|
| API | pytest 9 con Postgres real en CI y `pytest-cov` | Endpoints, reglas de negocio, permisos de `/api/admin/*` | Cobertura mínima del 80 % de las líneas; si baja, el check falla |
| Frontend | Vitest 5 con Testing Library | Componentes con lógica: selector de idioma, formularios, panel | Cobertura mínima del 80 % (era 60 %; Nicolas la subió el 2026-10-12) |
| E2E (de punta a punta) | Playwright 1.64 | La página carga en los dos idiomas, el formulario de contacto, y el login más crear un proyecto en el panel | Corre en cada PR, contra el `compose` levantado en el runner |
| Tipos y estilo | `ruff`, `mypy`, `tsc --strict`, ESLint y Prettier | Formato, errores comunes y tipos | Sin errores |

Las reglas de testing son:

- Cada `feature/*` trae sus tests.
- Cada `fix/*` trae un test que reproduce el error antes de corregirlo.
- Nunca se salta ni se desactiva un test para dejar el CI en verde. Un test inestable se arregla en su propio PR.
- La base no se reemplaza por mocks (objetos simulados) en los tests de la API: se prueba contra Postgres de verdad.
- `pre-commit` 4.6 corre `ruff`, Prettier y la detección de llaves privadas antes de cada commit, para encontrar los errores antes del CI.

### Validación de seguridad

| Control | Cuándo | Falla el check si |
|---|---|---|
| Secret scanning con push protection de GitHub (gratis en repos públicos) | En cada push | Se intenta subir un secreto (bloquea el push) |
| CodeQL (análisis estático de GitHub) para Python y TypeScript | En cada PR y cada semana | Hay un hallazgo de severidad alta o crítica |
| Reglas de seguridad de `ruff` (las de Bandit) | En cada PR | Hay cualquier hallazgo |
| `pip-audit` 2.10 y `npm audit --audit-level=high` | En cada PR y cada semana | Hay una dependencia con vulnerabilidad alta |
| Trivy (escáner de imágenes Docker) | En cada PR, sobre las imágenes construidas | Hay una vulnerabilidad alta o crítica con corrección disponible |
| Dependabot (alertas y PR de actualización) | Cada semana | No bloquea; los PR pasan por los mismos checks |

En cada PR también se revisan a mano estos puntos de la checklist:

- Las entradas se validan con Pydantic.
- Las rutas de administración tienen un test que prueba el acceso sin sesión.
- No se registran datos personales en los logs.

### Revisión automática con IA

Nicolas pidió, el 2026-10-11, que un agente revise los PR para que no se le pase nada importante en su propia revisión.

- **Herramienta:** `anthropics/claude-code-action@v1` en el workflow `ai-review.yml`.
- **Autenticación:** `CLAUDE_CODE_OAUTH_TOKEN`, generado con `claude setup-token`. Con eso, el uso se descuenta de la suscripción de Claude en vez de cobrarse por token. Si más adelante se usa una API key, se cobra aparte.
- **Cuándo corre:** al abrir un PR hacia `dev` y al marcarlo listo para revisión, no en cada push. También se puede pedir de nuevo comentando `@claude revisa`.
- **Cuándo no corre:** en los PR que solo cambian documentación (`docs/**`, `*.md`), en los de Dependabot y en los borradores.
- **Qué revisa:** el diff, contra las reglas de `docs/` (ADR, arquitectura) y de `CLAUDE.md`: errores, seguridad, tests faltantes y reglas no cumplidas.
- **Criterio (Nicolas, 2026-10-12):** "no overengineer" y "keep it simple and secure". Marca como importante solo lo que sea un riesgo real, y no propone capas ni abstracciones extra si lo simple ya es seguro.
- **Cómo responde:** solo con comentarios, como máximo unos 10, ordenados por severidad. **Nunca aprueba**, para que la aprobación de la ADR 0007 (tu bypass registrado) siga siendo una decisión tuya y no la active un bot.
- **No bloquea el merge:** es una ayuda para tu revisión, no un check obligatorio.

Costo estimado, sin medir: por PR de 300 a 800 líneas, entre 40.000 y 120.000 tokens de entrada y entre 3.000 y 8.000 de salida. Con caché y un modelo de gama media, cerca de un tercio menos. Con unos 25 PR en la versión 1, serían del orden de 1 a 3 millones de tokens de entrada en total. Se mide en los primeros 5 PR y, si consume demasiado de tu plan, se baja el tope de comentarios o se limita a los PR de `feature/*`.

### Check de despliegue

Son dos niveles, y el detalle está en la ADR 0008:

1. **En cada PR a `dev`:** el job `deploy-check` levanta `compose.prod.yml` en el runner de CI, con las imágenes del PR, y corre los E2E y `GET /api/health`.
2. **En el PR de versión a `main`:** se exige que staging esté desplegado con el mismo SHA y que sus E2E estén en verde.

### Definición de terminado de un PR

- [ ] Tests nuevos o actualizados, con la cobertura sobre el mínimo
- [ ] CI, seguridad y E2E en verde
- [ ] Sin secretos ni datos personales
- [ ] Documentación actualizada si cambia algo visible (README o docs/)
- [ ] Rama al día con su base
- [ ] Comentarios de la revisión automática atendidos o respondidos
- [ ] Aprobado, o mergeado por Nicolas con bypass registrado

## Consecuencias

- Nada llega a `dev` sin tests ni checks de seguridad, y nada llega a `main` sin pasar por staging.
- El historial de `dev` y `main` es lineal. A cambio, cada commit tiene que estar limpio antes del PR, y `dev` se resincroniza sola después de cada versión.
- El CI pasa de ~5 a unos ~8-10 minutos por los E2E y los escaneos. Se mantiene gratis en un repo público.
- Configurar todo esto agrega unas 6 h al hito 1 del plan, y `sync-dev.yml` suma ~1 h. Con staging (ADR 0008), la estimación sube de 80 a ~92 h.
- Las reglas quedan en la plantilla y en CLAUDE.md, así que Claude Code las sigue en cada producto nuevo.
