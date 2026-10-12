# Prompts de desarrollo · Sitio web de portafolio

Aquí queda cada prompt que se usa con Claude Code para una tarea del plan: qué se pidió, cuánto costó y qué se aprendió. Sirve para tres cosas:

- Reutilizar los prompts que funcionaron en la siguiente idea.
- Medir el uso de tokens por tarea (ADR 0009).
- Ver el avance del desarrollo prompt a prompt.

## Cómo se usa

1. Antes de empezar una tarea del plan, copia `plantilla.md` a `NNNN-<tarea>.md`, por ejemplo `0001-estructura-monorepo.md`, y complétala. El número es correlativo.
2. Pega el bloque "Prompt" en una sesión nueva de Claude Code.
3. Al terminar, completa la sección "Resultado" del archivo y agrega una fila a `registro.md`.
4. Si hubo que corregir el prompt, se guarda la versión que funcionó y se anota en "Lecciones" qué cambió.

Claude Code puede llenar el registro al final de cada sesión si se le pide: "agrega la fila de esta tarea a `prompts/registro.md` con el uso de `/cost`". Esa instrucción queda en el CLAUDE.md del producto.
