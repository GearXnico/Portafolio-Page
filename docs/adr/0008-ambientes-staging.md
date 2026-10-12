# 0008 · Ambientes: staging antes de producción

Estado: aceptada · Fecha: 2026-10-11 · Pidió: Nicolas

## Contexto

Nicolas pidió un ambiente de staging para probar antes de pasar a producción. Debe simular `main` y servir para correr pruebas de producción. También pidió evaluar dos ambientes, `staging-dev` y `staging-main`, para reducir errores tanto en producción como en `dev`.

Hoy el VPS (servidor virtual privado) de producción tiene 1 GiB de memoria. Ahí corren Postgres, la API y Caddy, y no queda espacio para una segunda copia del sitio.

Con rebase & merge (ADR 0007), lo que está en `dev` al abrir el PR de versión es exactamente lo que va a quedar en `main`. Por eso un `staging-dev` y un `staging-main` permanentes mostrarían casi siempre el mismo código.

## Opciones consideradas

| Opción | Qué es | Costo mensual extra | Trabajo extra | Contras |
|---|---|---|---|---|
| **A. Staging efímero por PR y staging permanente** | `staging-dev`: el sitio completo levantado en el runner de CI en cada PR a `dev`, que se destruye al terminar. `staging-main`: un VPS aparte que replica producción y se despliega con cada merge a `dev`. | US$6 (DigitalOcean 1 GiB, sin respaldo) | ~5 h | `staging-dev` no tiene URL (dirección web) para mirarlo a mano; solo corre pruebas automáticas |
| B. Dos staging permanentes | Un VPS de 2 GiB con `staging-dev` (cada merge a `dev`) y `staging-main` (cada PR de versión), en subdominios distintos | US$12 | ~7 h | Casi siempre muestran el mismo código, por el rebase & merge |
| C. Staging en el mismo VPS de producción | Se sube producción a 2 GiB y staging corre al lado | US$7,20 (de US$7,20 a US$14,40) | ~4 h | Una prueba pesada en staging puede botar producción |

Precios de DigitalOcean revisados el 2026-10-11: US$6 por 1 GiB y US$12 por 2 GiB al mes.

## Decisión

**A: staging efímero por PR y staging permanente en un VPS aparte** (Nicolas, 2026-10-11). Cubre los dos niveles que pidió por US$6 al mes, aísla producción, y el mismo VPS de staging sirve para los próximos productos.

Esto rige con cualquier opción:

- **Simular `main`:** staging usa el mismo `compose.prod.yml`, las mismas imágenes por SHA, el mismo script de despliegue (respaldo, migraciones y health check) y la misma versión de Postgres que producción.
- **Datos:** semilla de prueba más una copia del contenido público de producción (perfil, experiencia y proyectos). Nunca se copian mensajes de contacto ni visitas, porque tienen datos personales.
- **Secretos propios:** el correo de staging no se envía a nadie; se escribe en el log.
- **Acceso:** se publica en `staging.<dominio>` con usuario y contraseña en Caddy, y con `noindex` para que Google no lo indexe.
- **Gate a producción:** el PR de versión `dev` → `main` solo se puede mergear si staging está desplegado con el mismo SHA y sus E2E (pruebas de punta a punta) pasaron. Los E2E de staging prueban las mismas rutas que se probarán en producción.
- **Workflows:** `deploy.yml` recibe el ambiente (`staging` o `production`) como parámetro. Cada ambiente de GitHub tiene sus propios secretos de SSH (acceso remoto cifrado).

## Consecuencias

- Antes de llegar a producción, cada cambio se prueba dos veces: en el runner, con cada PR, y en staging, con cada merge a `dev`.
- El costo fijo sube de ~US$7,20 a ~US$13,20 al mes con la opción A.
- La estimación del brief sube a ~92 h, sumando esta ADR y la 0007. La fecha objetivo se corre del 2026-10-25 al ~2026-10-27; el escenario pesimista sigue siendo el 2026-10-30.
- Las migraciones se prueban contra una base con la forma de producción antes de aplicarse en producción.
