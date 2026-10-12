# 0001 · Despliegue en VPS con Docker Compose y Caddy

Estado: aceptada · Fecha: 2026-10-11 · Decidió: Nicolas

## Contexto

El sitio necesita un frontend, una API (interfaz de programación) y Postgres siempre disponibles, porque la primera visita de un reclutador no puede tardar en cargar. El despliegue es un área que Nicolas quiere reforzar y también algo que piden las ofertas de trabajo revisadas. Además, el servidor debería servir para los próximos productos del ecosistema sin multiplicar el costo.

## Opciones consideradas

| Opción | Costo mensual | Trabajo extra | Contras |
|---|---|---|---|
| A. VPS (servidor virtual privado) en DigitalOcean, 1 vCPU (procesador virtual) y 1 GiB de memoria, con respaldo semanal | US$7,20 | ~6 h | Hay que mantener el servidor |
| B. Render (API más Postgres administrados) | US$13 | ~1-2 h | Cada producto nuevo suma lo mismo |
| C. Fly.io más Neon más hosting estático | ~US$2-4 | ~4 h | La API y la base se duermen; tres proveedores |

Precios revisados el 2026-10-11 en las páginas oficiales.

## Decisión

A: un VPS en DigitalOcean (región Nueva York) con Docker Compose. Caddy 2.11 sirve el frontend, pasa `/api` a FastAPI y renueva solo el certificado HTTPS (conexión cifrada). Las imágenes se construyen en GitHub Actions, no en el servidor.

## Consecuencias

- Es la opción más barata sin arranques lentos, y la misma máquina aloja los próximos productos.
- Nicolas mantiene el servidor: acceso SSH (acceso remoto cifrado) solo con llave, firewall, parches automáticos y alertas de disco.
- La configuración (Compose, Caddyfile y scripts) queda en la plantilla y se reutiliza.
- Con 1 GiB de memoria no se puede construir en el servidor. Si un producto futuro necesita más, se sube de plan (US$12 por 2 GiB).
