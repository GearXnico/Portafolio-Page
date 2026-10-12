# 0009 · Uso eficiente de tokens sin perder calidad

Estado: aceptada · Fecha: 2026-10-11 · Pidió: Nicolas

## Contexto

El desarrollo se hace con Claude Code sobre una suscripción con límites de uso, y la revisión automática con IA de la ADR 0007 consume de la misma suscripción. El objetivo es sacarle el mayor provecho a cada token. La condición es no perder calidad: los tests, la seguridad y la revisión no se recortan para ahorrar.

En la práctica, lo que más gasta no es escribir código: es releer contexto que no hace falta, las sesiones largas que arrastran todo el historial, y rehacer trabajo cuando una tarea quedó mal definida.

## Opciones consideradas

| Opción | Ahorro | Contras |
|---|---|---|
| A. Sin reglas: trabajar como salga | Ninguno | Sesiones largas, mucho contexto repetido, límites del plan alcanzados a mitad de semana |
| B. Reglas de sesión, prompts y medición (esta ADR) | Alto en contexto y retrabajo | Disciplina: una tarea por sesión y llenar el registro |
| C. Usar siempre el modelo más barato | Alto por token | Más errores y retrabajo en tareas difíciles, así que el ahorro real es menor |

## Decisión

B, con estas reglas.

**Contexto mínimo**

- CLAUDE.md tiene menos de 200 líneas y apunta a los documentos de `docs/` en vez de copiarlos. Cada prompt dice qué documento y qué sección leer.
- `node_modules/`, `dist/`, `.venv/`, los lockfiles y `/media` quedan bloqueados para lectura en `.claude/settings.json`.
- En los prompts se nombran rutas y funciones; no se pega contenido que Claude puede leer solo.
- Las búsquedas amplias en el código se delegan a un subagente, que devuelve solo la conclusión.

**Sesiones cortas**

- Una tarea del plan por sesión. Al terminarla, `/clear` antes de la siguiente.
- Si una sesión se alarga, `/compact` con una indicación de qué conservar.
- Si una tarea no se termina en dos intentos, se divide en tareas más chicas en el plan; no se reintenta con un prompt más largo.

**Menos retrabajo**

- Las tareas que tocan varios archivos parten en modo plan: Claude propone, Nicolas aprueba y después se escribe.
- Cada prompt sale de la plantilla `prompts/plantilla.md`, con el criterio de terminado copiado del plan.
- Los hooks de `pre-commit` y los tests locales corren antes del PR, para no gastar una revisión de IA ni un ciclo de CI en errores de formato.
- La salida de tests y lint se pide resumida (`pytest -q --maxfail=1`, solo los errores del lint).

**Modelo según la tarea**

| Tipo de tarea | Modelo |
|---|---|
| Rutinaria (CRUD, componentes, tests, configuración) | Sonnet, de gama media |
| Diseño, errores difíciles, seguridad o una tarea que falló una vez | Opus, el más capaz |
| Revisión automática de PR | Sonnet, con el tope de comentarios de la ADR 0007 |

**Medición**

- Cada tarea registra sus tokens (`/cost`) en `prompts/registro.md`.
- Al cerrar cada hito se comparan los tokens y las horas con el plan, y se anota en `notas/` qué ajustar.
- Si un hito consume más del doble que el anterior por tarea, se revisan los prompts antes de seguir.

**Lo que nunca se recorta**

Tests, cobertura mínima, checks de seguridad, staging, la revisión humana y la revisión con IA de los PR de `feature/*`.

## Consecuencias

- Al final de la versión 1 habrá datos reales de cuánto cuesta cada tipo de tarea. Con ellos se ajustan la plantilla y las estimaciones de la siguiente idea.
- Las reglas de sesión y de modelo quedan en el CLAUDE.md del producto, así que Claude Code las aplica sin que haya que repetirlas.
- Llenar el registro toma ~2 minutos por tarea. Claude Code puede hacerlo al final de la sesión si se le pide.
