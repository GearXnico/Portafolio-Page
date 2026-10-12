# Brief · Sitio web de portafolio

ID: 2026-10-08-sitio-portafolio · Activada: 2026-10-11

## Problema

Nicolas quiere mostrar su trabajo como desarrollador full stack, backend Python y con IA, tanto a equipos que contratan como a clientes de proyectos. Hoy no tiene un lugar donde quien lo evalúa vea en un minuto qué sabe hacer, qué ha construido y cómo contactarlo. GitHub muestra el código, pero no muestra bien los juegos ni las apps, ni las decisiones de arquitectura.

Las ofertas de trabajo revisadas no exigen portafolio. Sí piden React+TS, API en Python, SQL, tests, Docker, CI/CD y despliegue. Por eso la página vale por dos cosas: lo que muestra y cómo está construida.

## Usuarios y sus tareas principales

| Usuario | Tarea | Qué necesita ver o hacer |
|---|---|---|
| Reclutador o líder técnico (llega desde una postulación) | Decidir en 1-2 minutos si vale la pena una entrevista | Perfil, stack, experiencia y proyectos con demo, todo en una página y en su idioma |
| Cliente referido (pyme que llega por recomendación) | Verificar que Nicolas es confiable y escribirle | Servicios, un caso escrito y un formulario de contacto |
| Nicolas (administrador) | Mantener el portafolio al día sin tocar código, y saber qué postulación o referido trajo visitas | Panel de administración simple; visitas y contactos por enlace |

## Alcance del MVP (versión 1)

1. Página única con perfil (texto, sin foto), habilidades, experiencia y contacto.
2. **Español e inglés según la ubicación del visitante**, con un selector para cambiar de idioma a mano. Todo el contenido editable existe en los dos idiomas.
3. Sección de proyectos servida por la API. El primer caso es la propia página: arquitectura, pipeline y qué hizo la IA y qué decidió Nicolas.
4. **Panel de administración** con un solo usuario (Nicolas), protegido con contraseña. Permite crear, editar, ordenar y ocultar proyectos (título, descripción en los dos idiomas, stack, enlaces a demo y repositorio, capturas) y editar el perfil, las habilidades y la experiencia. También muestra los mensajes de contacto y las visitas por enlace. La meta es que agregar un proyecto tome menos de 10 minutos.
5. Formulario de contacto que guarda el mensaje y avisa a Nicolas por correo.
6. Enlaces con UTM por postulación y por referido. Un UTM es un parámetro que se agrega al final del enlace para saber de dónde viene la visita, por ejemplo `?utm_source=portal&utm_campaign=empresa-x`. Así cada postulación o referido tiene su propio enlace, y el sitio registra cuántas visitas y contactos trajo cada uno.
7. Pieza técnica completa: frontend en React+TS, API en FastAPI, Postgres, tests (pytest y frontend), Docker y GitHub Actions que prueba y despliega en cada merge.
8. La plantilla del repositorio (pruebas, CI y despliegue) queda separada y reutilizable para el siguiente producto.

## Fuera del MVP

- Blog y editor de texto enriquecido: las descripciones son texto simple o Markdown.
- Más de un usuario administrador o roles.
- Video o foto de Nicolas (regla de no ser rostro público).
- Juegos o apps embebidos: se agregan desde el panel cuando existan, como enlace con captura.
- Los agentes de la fábrica de software (issue → PR). Solo se hace la plantilla.
- Dominio propio, si complica el despliegue de la primera semana: se puede publicar primero con el subdominio del hosting.

## Tiempo de desarrollo estimado

Estimación a 40 h por semana. Supone que Claude Code escribe gran parte del código y que React y el despliegue toman más tiempo que el resto, porque son tus puntos más débiles.

| Bloque | Horas |
|---|---|
| Plantilla del repositorio: estructura, Docker, tests y CI/CD con despliegue de una página vacía | 14 |
| API y base de datos: proyectos, perfil, contacto y visitas por UTM | 14 |
| Frontend público: página, sección de proyectos e idiomas según ubicación | 18 |
| Panel de administración: login y edición de proyectos, perfil y mensajes | 18 |
| Contenido en dos idiomas y caso de la propia página | 8 |
| Pruebas finales, ajustes y publicación | 8 |
| **Total** | **80 h (unas 2 semanas)** |

Rango: entre 65 h (optimista) y 110 h (pesimista, si el despliegue o el panel se complican). Fecha objetivo de la versión 1: **2026-10-25**; con el escenario pesimista, 2026-10-30.

## Métricas de éxito

Del portafolio como producto:

- **Más de 1 desarrollo nuevo agregado al portafolio en menos de 1 mes desde la publicación.**
- Visitas desde 5 postulaciones o más en las primeras 8 semanas.
- Al menos una entrevista en que lo mencionen o un contacto de un cliente por el formulario.

Técnicas, de la versión 1:

- Despliegue automático en cada merge a la rama principal, con tests verdes en CI.
- Agregar un proyecto desde el panel toma menos de 10 minutos.
- La plantilla permite partir el siguiente producto en 1 día o menos.

## Criterio de abandono

No aplica. Es el portafolio propio y se mantiene en el tiempo (decisión de Nicolas, 2026-10-11).

## Supuestos a confirmar

- Sin foto.
- El formulario avisa por correo.
