# 0002 · Idioma según el navegador, con detección por país para después

Estado: aceptada · Fecha: 2026-10-11 · Decidió: Nicolas

## Contexto

El brief pide el sitio en español o en inglés según la ubicación del visitante, con un selector manual. Detectar la ubicación exige un servicio o una base de datos de IP (dirección de red). Para la versión 1 importa más publicar a tiempo.

## Opciones consideradas

| Opción | Costo | Contras |
|---|---|---|
| A. País desde Cloudflare (header `CF-IPCountry`, plan gratis) | ~1 h | El DNS (sistema de nombres de dominio) pasa a Cloudflare; un proveedor más |
| B. País por IP con la base GeoLite2 de MaxMind | ~3 h más actualizaciones mensuales | Más piezas para lo mismo |
| C. Idioma del navegador (`Accept-Language`) | 0 h | Es el idioma del visitante, no su ubicación |

## Decisión

C en la versión 1 y A cuando el sitio crezca. Si el primer idioma del navegador es español, la página sale en español; si no, en inglés. La elección del selector se guarda en `localStorage` y manda sobre todo lo demás.

## Consecuencias

- No hay proveedores extra ni trabajo adicional en la versión 1.
- Un reclutador en Chile con el navegador en inglés verá la página en inglés. Es aceptable, porque es el idioma que usa.
- Para que pasar a A sea un cambio chico, la API decide el idioma en una sola función, que recibe el país (vacío por ahora) y el `Accept-Language`. La tabla de visitas ya tiene la columna `country`.
