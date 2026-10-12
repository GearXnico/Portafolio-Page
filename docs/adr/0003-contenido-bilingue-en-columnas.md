# 0003 · Contenido bilingüe en columnas `_es` y `_en`

Estado: aceptada · Fecha: 2026-10-11 · Propuso: Claude, aprobada con la arquitectura

## Contexto

Todo el contenido editable (perfil, experiencia, proyectos y textos alternativos de las imágenes) existe en español y en inglés. Son dos idiomas fijos y no se planea agregar más.

## Opciones consideradas

| Opción | Costo | Contras |
|---|---|---|
| A. Columnas por idioma (`title_es`, `title_en`) | El más bajo | Agregar un tercer idioma obliga a una migración por tabla |
| B. Tabla de traducciones (entidad, campo, idioma, texto) | ~4 h extra entre API y panel | Consultas y formularios más complejos |
| C. Archivos JSON de traducción en el frontend | Bajo para textos fijos | El contenido no se podría editar desde el panel |

## Decisión

A para el contenido de la base. Los textos fijos de la interfaz (botones y títulos) van en archivos JSON del frontend, que no se editan desde el panel.

## Consecuencias

- El formulario del panel muestra los dos idiomas lado a lado, lo que ayuda a no olvidar una traducción.
- La API devuelve los dos idiomas y el frontend elige cuál mostrar, así que cambiar de idioma no requiere otra llamada.
- Un tercer idioma costaría una migración por tabla. Se acepta porque no está en los planes.
