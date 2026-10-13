# Reglas de testing

Qué se prueba, qué no, y por qué existe cada tipo de prueba. Los comandos están en el README y las reglas obligatorias en la ADR (registro de decisión de arquitectura) 0007.

## Para qué sirven los tests aquí

Un test vale si falla cuando algo que importa se rompe. En este proyecto importan dos cosas:

1. **Lo que ve el visitante y el administrador:** que la página cargue con su contenido, en su idioma, y que el panel deje editarla.
2. **Las reglas que pueden romperse en silencio:** las que, si fallan, nadie lo nota al mirar la página, pero abren un problema de seguridad o de datos. Por ejemplo, una ruta del panel que responde sin sesión.

Todo test nuevo tiene que proteger una de esas dos cosas. Si no, no se escribe.

## Los tipos de prueba y por qué existe cada uno

| Tipo | Herramienta | Dónde | Por qué existe |
|---|---|---|---|
| E2E (prueba de punta a punta) | Playwright | `web/e2e/` | Es la única que prueba el sistema entero como lo usa una persona: navegador, Caddy, API y base. Si algo entre las piezas se desconecta, solo esta lo ve. |
| API | pytest contra Postgres real | `api/tests/` | Prueba las reglas de negocio y de seguridad de cada ruta, rápido y sin navegador. Va contra Postgres de verdad porque varias reglas viven en la base (restricciones, permisos del usuario de la API) y un mock (objeto simulado) las ocultaría. |
| Componentes web | Vitest y Testing Library | `web/tests/` | Prueba la lógica de la página que no necesita la API: qué se muestra con cada respuesta, el idioma, los enlaces. Corre en segundos. |
| Estáticas | ruff, mypy, `tsc`, ESLint y Prettier | CI y pre-commit | Atrapan errores de tipos, de estilo y patrones inseguros sin ejecutar nada. |
| Producción en el runner | job `deploy-check` | `.github/workflows/ci.yml` | Levanta `deploy/compose.prod.yml` y corre los E2E contra él, para saber que lo que se despliega arranca. |

Regla práctica para elegir el nivel: **un caso se prueba una vez, en el nivel más bajo que lo puede ver**. Una validación de un campo va en pytest; que el formulario completo llegue a la base va en un E2E. No se repite el mismo caso en los tres niveles.

## Qué se prueba siempre

| Regla | Por qué | Dónde se prueba hoy |
|---|---|---|
| Toda ruta de `/api/admin/*` responde 401 sin sesión | Una ruta nueva fuera del router protegido dejaría el panel abierto | `test_admin_login.py` (recorre todas las rutas). `test_admin_content.py` lo repite para las rutas de contenido con un cuerpo vacío, para comprobar además que el 401 llega antes que el 422; el PR #24 propone unirlos |
| Login: clave correcta, incorrecta, bloqueo tras 5 intentos, sesión inválida o vencida | Es la única puerta del panel | `test_admin_login.py` |
| En la web, `/admin` sin sesión lleva al login, y el login y el logout muestran lo que corresponde a cada respuesta de la API | Si falla, el panel se ve vacío o con errores en vez de pedir la clave (la API igual responde 401) | `web/e2e/admin.spec.ts` (redirección, y entrar y salir con la clave real) y `web/tests/admin.test.tsx` (mensajes y logout) |
| Validación de capturas: tipo real del archivo, 5 MB, píxeles, metadatos | Un archivo subido es la entrada más peligrosa | `test_admin_content.py` |
| Límites de envío: 5 mensajes por hora por IP, honeypot (campo trampa), tamaño del cuerpo | Sin ellos el formulario se llena de spam | `test_contact.py` y `test_rate_limit.py` |
| La IP real detrás de Caddy, y que `X-Forwarded-For` no se crea sin proxy de confianza | Si falla, un atacante se salta los límites cambiando un header | `test_contact.py` (contacto) y `test_admin_login.py` (login): son dos casos, uno por ruta, porque cada una puede quedar mal configurada por separado |
| Toda entrada inválida responde 422 | Pydantic valida, pero el test confirma que el esquema es el correcto | Un test por recurso |
| Lo que no debe salir no sale: correo del perfil, IP del visitante, ids internos | Una fuga de datos personales no se ve en la página | `test_bootstrap.py` y `test_admin_content.py` |
| El usuario de la API no puede cambiar tablas | Limita el daño de una inyección de SQL | `test_permisos_db.py` |
| Las migraciones se aplican, se revierten y calzan con los modelos | Una migración rota tumba el despliegue | `test_migrations.py` |
| Un mensaje enviado desde el formulario de contacto llega a la API y se guarda | Es la única forma de contacto; si el formulario y la API dejan de calzar, nadie avisa | `web/e2e/contact.spec.ts` (el 201 llega solo después de guardar, como prueba `test_contact.py`) |
| La página carga, cambia de idioma y no tiene errores de consola ni le faltan cabeceras de seguridad | Es lo que ve cualquier visitante | `web/e2e/` |

Cada `fix/*` empieza con un test que reproduce el error y falla antes de la corrección.

## Qué no se prueba

- **Lo que ya prueban las librerías:** que FastAPI devuelva JSON o que React renderice. Sí se prueba que *nuestro* esquema rechace lo que debe.
- **Estilos y textos exactos:** colores, márgenes o la redacción de un título. Se prueba que el texto venga del idioma correcto, no qué dice.
- **Código sin lógica:** un modelo que solo declara columnas, un componente que solo pinta lo que recibe.
- **El mismo caso en varios niveles:** ver la regla práctica de arriba.
- **Detalles internos:** se prueba lo que entra y lo que sale (la respuesta, la fila en la base), no cómo lo hace la función por dentro. Así un refactor no rompe tests.

## Cobertura

**Los tests tienen que cubrir como mínimo el 80 % de las líneas del código**, en la API y en web (ADR 0007). Si un PR baja de ese mínimo, el CI falla y no se puede mergear.

El mínimo es obligatorio, pero no es la meta: asegura que no quede código sin probar, no que se haya probado lo importante. Para eso están las tablas de arriba. Si falta cobertura, se agregan tests de lo que importa del código nuevo, no tests vacíos que solo suben el número.

## Cómo se escribe un test

- **Nombre en español que diga el comportamiento:** `test_bloquea_tras_5_intentos_fallidos`, no `test_login_3`. Al leer la lista de nombres se entiende qué hace el sistema.
- **Un comportamiento por test**, con tres partes: preparar, actuar y comprobar.
- **Datos de mentira y claros:** IP de documentación (`203.0.113.7`), correos `@example.com`. Nunca datos reales.
- **Nunca** se salta, desactiva ni borra un test para dejar el CI en verde. Un test inestable se arregla en su propio PR (pull request).
- Si un test se vuelve redundante, se propone borrarlo en el PR y el dueño del proyecto lo confirma.
