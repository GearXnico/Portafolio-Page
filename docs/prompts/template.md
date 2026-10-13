# NNNN · <tarea del plan>

Tarea del plan: <número, por ejemplo 1.2> · Fecha: AAAA-MM-DD · Modelo: <Sonnet / Opus> · Rama: `feature/<nombre>`

## Prompt

```
Tarea <número> del plan (docs/plan.md): <título de la tarea>.

Contexto: lee solo docs/plan.md (tarea <número>) y <ADR o sección de arquitectura que aplique>. No leas otros documentos salvo que los necesites.

Qué hacer:
- <paso concreto 1>
- <paso concreto 2>

Terminado cuando: <criterio de terminado copiado del plan>.

Restricciones:
- Sigue CLAUDE.md (ramas, commits, tests, seguridad).
- Corre los tests y el lint antes de terminar y muéstrame solo el resumen.
- Si algo del plan no calza con el código, pregúntame antes de cambiar el diseño.

Al terminar: abre el PR a dev y dame el enlace.
```

## Resultado

- PR: <enlace>
- Tokens (de `/cost`): <entrada> / <salida> · Duración: <min>
- ¿Se terminó en una sesión?: sí / no (por qué)
- Intentos: <1, 2…>

## Lecciones

- <Qué funcionó, qué hubo que aclarar y qué cambiaría en el prompt la próxima vez.>
