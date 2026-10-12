# Reglas de desarrollo

Cómo se construye este repositorio. Es la versión corta: el porqué de cada regla está en la ADR (registro de decisión de arquitectura) 0007, y los comandos en el README.

## Principio

**No overengineer. Keep it simple and secure.** Ante dos soluciones seguras, se elige la más simple. La seguridad no se recorta: se resuelve con lo más directo que funcione.

La idea de fondo es que el dueño del proyecto pueda leer cualquier parte del código y entender qué hace y por qué. Código que nadie entiende no se puede mantener ni defender en una entrevista.

## Qué se construye ahora

- Solo lo que nombra una tarea de `docs/plan.md`, dentro del alcance de `docs/brief.md`.
- Lo que el brief deja en "Fuera del MVP" no se adelanta, aunque parezca fácil.
- Si una tarea necesita algo que el plan no nombra (una tabla, un servicio, una dependencia), se pregunta antes y, si se aprueba, se anota en el plan o en una ADR.

## Cuándo no crear una capa

Antes de agregar una abstracción, una variable de configuración o un archivo nuevo, revisa esta lista. Si la respuesta es "no", no se agrega.

| Antes de... | Pregúntate | Ejemplo de "no" |
|---|---|---|
| Extraer una función o clase compartida | ¿Ya hay tres lugares que la usan igual? | Dos rutas con un `if` parecido: se deja repetido |
| Agregar una variable de entorno | ¿Cambia entre local, staging y producción, o es un secreto? | El largo máximo de un mensaje va en el código |
| Crear una tabla o columna | ¿Lo pide el plan o el modelo de datos de `docs/arquitectura.md`? | Una tabla de usuarios cuando hay un solo administrador (ADR 0004) |
| Agregar una dependencia | ¿Lo que ya está instalado no alcanza, y pasa `pip-audit` o `npm audit`? | Una librería de fechas para formatear mes y año |
| Hacer algo configurable | ¿Hoy hay dos casos reales? | Soportar un tercer idioma "por si acaso" cuando el brief pide español e inglés |

Hay dos excepciones decididas a propósito: el idioma se decide solo en `api/app/services/locale.py` (ADR 0002) y el correo se envía solo desde `api/app/services/mail.py` (ADR 0005). Son un punto único porque se sabe que van a cambiar.

## Dónde va cada cosa

El mapa completo está en el README. Al escribir código:

- **API:** la ruta en `app/routers/` solo recibe, llama y responde. La lógica va en `app/services/`, la validación de lo que entra y sale en `app/schemas/` (Pydantic) y las tablas en `app/models/`.
- **Web:** una página por archivo en `src/pages/`, un componente por archivo en `src/components/`, las llamadas a la API en `src/api/` y los textos en `src/i18n/es.json` y `en.json`, nunca escritos dentro de un componente.
- **Nombres:** el código en inglés; los textos para el usuario, los tests y la documentación en español.
- **Comentarios:** explican el porqué, no el qué. Cada archivo de `services/` abre con un párrafo que dice de qué se encarga.

## Ramas, commits y PR (pull request)

Resumen de la ADR 0007:

1. Se parte desde `dev` en una rama `feature/`, `fix/`, `docs/` o `chore/` con 2 a 4 palabras en español, por ejemplo `feature/formulario-contacto`. `hotfix/` sale de `main`.
2. Commits con Conventional Commits (formato estándar de mensajes) en español: `feat: agrega formulario de contacto`. Cada commit hace una sola cosa y deja los tests en verde, porque llega tal cual a `dev`.
3. Un PR por tarea del plan, hacia `dev`, idealmente con menos de ~400 líneas, con la plantilla: Antes, Después, Cómo probar y la checklist.
4. Se mergea solo con rebase & merge, y la rama se borra después.
5. Nunca se suben secretos, `.env` ni datos personales: el repositorio es público.

## Cómo se revisa un PR

1. **CI (integración continua):** tests, lint, tipos, seguridad y E2E (prueba de punta a punta) tienen que estar en verde. Sin eso no se puede mergear.
2. **Revisión con IA:** `ai-review.yml` deja comentarios en los PR de código, nunca aprueba y no bloquea. Cada comentario se corrige o se responde en su hilo.
3. **Revisión del dueño:** lee el PR en este orden y lo aprueba (o mergea con bypass registrado) solo si responde que sí a todo:
   - ¿Hace lo que pide la tarea, y nada más?
   - ¿Entiendo cada archivo que cambió? Si no, se pide una explicación en el PR antes de seguir.
   - ¿Es lo más simple que funciona? (tabla de arriba)
   - ¿Las entradas se validan, las rutas de `/api/admin/*` exigen sesión y los logs no guardan datos personales?
   - ¿Los tests prueban lo que importa? (`docs/testing.md`)
   - ¿El README o `docs/` quedaron al día si cambió algo visible?

Para entender un PR grande, conviene leerlo commit por commit: cada uno hace una sola cosa y su mensaje dice cuál.
